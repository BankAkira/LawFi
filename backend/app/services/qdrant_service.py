import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)

from app.config import settings


class QdrantService:
    """Service for vector search operations with Qdrant."""

    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection = settings.qdrant_collection

    def ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_ruling(
        self,
        ruling_id: int,
        embedding: list[float],
        metadata: dict,
    ) -> str:
        """Insert or update a ruling vector in Qdrant."""
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "ruling_id": ruling_id,
                        "ruling_number": metadata.get("ruling_number", ""),
                        "year": metadata.get("year", 0),
                        "case_type": metadata.get("case_type", ""),
                        "result": metadata.get("result", ""),
                        "keywords": metadata.get("keywords", []),
                    },
                )
            ],
        )
        return point_id

    def search(
        self,
        query_vector: list[float],
        limit: int = 20,
        case_type: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        result_filter: str | None = None,
    ) -> list[dict]:
        """Semantic search with optional filters."""
        must_conditions = []

        if case_type:
            must_conditions.append(
                FieldCondition(key="case_type", match=MatchValue(value=case_type))
            )
        if result_filter:
            must_conditions.append(
                FieldCondition(key="result", match=MatchValue(value=result_filter))
            )
        if year_from or year_to:
            range_params = {}
            if year_from:
                range_params["gte"] = year_from
            if year_to:
                range_params["lte"] = year_to
            must_conditions.append(
                FieldCondition(key="year", range=Range(**range_params))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        return [
            {
                "ruling_id": hit.payload.get("ruling_id"),
                "score": hit.score,
                "ruling_number": hit.payload.get("ruling_number"),
            }
            for hit in results
        ]

    def delete_ruling(self, qdrant_id: str) -> None:
        """Delete a ruling vector from Qdrant."""
        self.client.delete(
            collection_name=self.collection,
            points_selector=[qdrant_id],
        )
