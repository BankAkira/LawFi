from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_rulings(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search rulings with hybrid keyword + semantic search."""
    service = SearchService(db)
    return await service.search(request, user)


@router.get("/suggest")
async def suggest(
    q: str,
    db: AsyncSession = Depends(get_db),
):
    """Auto-suggest for search queries (public, no auth required)."""
    service = SearchService(db)
    return await service.suggest(q)
