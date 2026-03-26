from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.search_history import SearchHistory
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


class SearchHistoryResponse(BaseModel):
    id: int
    query: str
    search_type: str
    results_count: int
    filters_applied: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[SearchHistoryResponse])
async def list_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List search history for the current user, most recent first."""
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()
