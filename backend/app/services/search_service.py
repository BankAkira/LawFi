from datetime import UTC, date, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ruling import Ruling
from app.models.search_history import SearchHistory
from app.models.user import SubscriptionTier, User
from app.schemas.ruling import RulingListItem
from app.schemas.search import SearchRequest, SearchResponse

# Lazy imports: these depend on google-cloud and qdrant-client which may not
# be installed in test environments.  Imported inside the methods that need them.


class SearchService:
    """Hybrid search combining PostgreSQL full-text and Qdrant semantic search."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, request: SearchRequest, user: User) -> SearchResponse:
        """Execute hybrid search and return results."""
        # Check rate limits
        await self._check_rate_limit(user)

        # Run both searches
        keyword_results = await self._keyword_search(request)
        semantic_results = await self._semantic_search(request)

        # Merge results with weighted scores
        merged = self._merge_results(keyword_results, semantic_results)

        # Paginate
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        page_results = merged[start:end]

        # Fetch full ruling data for results
        if page_results:
            ruling_ids = [r["ruling_id"] for r in page_results]
            result = await self.db.execute(
                select(Ruling).where(Ruling.id.in_(ruling_ids))
            )
            rulings_map = {r.id: r for r in result.scalars().all()}

            items = []
            for r in page_results:
                ruling = rulings_map.get(r["ruling_id"])
                if ruling:
                    item = RulingListItem(
                        id=ruling.id,
                        ruling_number=ruling.ruling_number,
                        year=ruling.year,
                        case_type=ruling.case_type,
                        result=ruling.result,
                        summary=ruling.summary,
                        keywords=ruling.keywords,
                        relevance_score=r.get("score"),
                    )
                    items.append(item)
        else:
            items = []

        # Log search history
        await self._log_search(user.id, request, len(merged))

        # Update daily search count
        await self._increment_search_count(user)

        return SearchResponse(
            results=items,
            total=len(merged),
            page=request.page,
            page_size=request.page_size,
            query=request.query,
        )

    async def suggest(self, query: str) -> list[str]:
        """Auto-suggest based on ruling numbers and keywords."""
        suggestions = []

        # Suggest matching ruling numbers
        result = await self.db.execute(
            select(Ruling.ruling_number)
            .where(Ruling.ruling_number.ilike(f"%{query}%"))
            .limit(5)
        )
        suggestions.extend([f"ฎีกา {r}" for r in result.scalars().all()])

        return suggestions[:10]

    async def _keyword_search(self, request: SearchRequest) -> list[dict]:
        """PostgreSQL full-text search."""
        query = select(Ruling.id, Ruling.ruling_number).where(
            Ruling.is_processed == True  # noqa: E712
        )

        # Text search across full_text, summary, facts, issues, judgment
        if request.query:
            search_term = f"%{request.query}%"
            query = query.where(
                or_(
                    Ruling.full_text.ilike(search_term),
                    Ruling.summary.ilike(search_term),
                    Ruling.ruling_number.ilike(search_term),
                    Ruling.facts.ilike(search_term),
                    Ruling.issues.ilike(search_term),
                    Ruling.judgment.ilike(search_term),
                )
            )

        # Apply filters
        query = self._apply_filters(query, request)
        query = query.limit(settings.search_results_limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {"ruling_id": row.id, "score": 1.0, "source": "keyword"} for row in rows
        ]

    async def _semantic_search(self, request: SearchRequest) -> list[dict]:
        """Qdrant vector similarity search."""
        try:
            from app.services.embedding_service import EmbeddingService
            from app.services.qdrant_service import QdrantService

            embedding_service = EmbeddingService()
            query_vector = embedding_service.embed_text(request.query)

            qdrant = QdrantService()
            results = qdrant.search(
                query_vector=query_vector,
                limit=settings.search_results_limit,
                case_type=request.case_type.value if request.case_type else None,
                year_from=request.year_from,
                year_to=request.year_to,
                result_filter=request.result.value if request.result else None,
            )

            return [
                {
                    "ruling_id": r["ruling_id"],
                    "score": r["score"],
                    "source": "semantic",
                }
                for r in results
            ]
        except Exception:
            # Fallback: if Qdrant/embedding unavailable, return empty
            return []

    def _merge_results(
        self,
        keyword_results: list[dict],
        semantic_results: list[dict],
    ) -> list[dict]:
        """Merge keyword and semantic results with weighted scoring."""
        scores: dict[int, float] = {}

        kw = settings.keyword_search_weight
        sw = settings.semantic_search_weight

        for r in keyword_results:
            rid = r["ruling_id"]
            scores[rid] = scores.get(rid, 0) + r["score"] * kw

        for r in semantic_results:
            rid = r["ruling_id"]
            scores[rid] = scores.get(rid, 0) + r["score"] * sw

        merged = [{"ruling_id": rid, "score": score} for rid, score in scores.items()]
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged

    def _apply_filters(self, query: Select, request: SearchRequest) -> Select:
        """Apply filter conditions to a SQLAlchemy query."""
        if request.case_type:
            query = query.where(Ruling.case_type == request.case_type)
        if request.year_from:
            query = query.where(Ruling.year >= request.year_from)
        if request.year_to:
            query = query.where(Ruling.year <= request.year_to)
        if request.result:
            query = query.where(Ruling.result == request.result)
        return query

    async def _check_rate_limit(self, user: User) -> None:
        """Check if user has exceeded daily search limit."""
        if user.subscription_tier != SubscriptionTier.FREE:
            return

        today = date.today()
        if user.last_search_date and user.last_search_date.date() == today:
            if user.daily_search_count >= settings.free_daily_searches:
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"ถึงขีดจำกัดการค้นหารายวัน ({settings.free_daily_searches} ครั้ง/วัน) กรุณาอัปเกรดเป็น Pro",
                )

    async def _increment_search_count(self, user: User) -> None:
        """Increment user's daily search count."""
        today = date.today()
        if user.last_search_date is None or user.last_search_date.date() != today:
            user.daily_search_count = 1
            user.last_search_date = datetime.now(UTC)
        else:
            user.daily_search_count += 1
        await self.db.commit()

    async def _log_search(
        self, user_id: int, request: SearchRequest, results_count: int
    ) -> None:
        """Log search to history."""
        import json

        filters = {}
        if request.case_type:
            filters["case_type"] = request.case_type.value
        if request.year_from:
            filters["year_from"] = request.year_from
        if request.year_to:
            filters["year_to"] = request.year_to
        if request.result:
            filters["result"] = request.result.value

        history = SearchHistory(
            user_id=user_id,
            query=request.query,
            search_type="hybrid",
            results_count=results_count,
            filters_applied=json.dumps(filters, ensure_ascii=False)
            if filters
            else None,
        )
        self.db.add(history)
        await self.db.commit()
