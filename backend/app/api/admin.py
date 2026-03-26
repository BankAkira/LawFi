from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ruling import Ruling
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Dependency: require admin privileges."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="สิทธิ์ admin เท่านั้น",
        )
    return user


@router.get("/stats")
async def admin_stats(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard stats: user counts, ruling counts, search counts."""
    total_users = await db.scalar(select(func.count(User.id)))
    total_rulings = await db.scalar(select(func.count(Ruling.id)))
    processed = await db.scalar(
        select(func.count(Ruling.id)).where(Ruling.is_processed == True)  # noqa: E712
    )
    failed = await db.scalar(
        select(func.count(Ruling.id)).where(Ruling.is_processed == False)  # noqa: E712
    )

    return {
        "total_users": total_users or 0,
        "total_rulings": total_rulings or 0,
        "processed_rulings": processed or 0,
        "failed_rulings": failed or 0,
    }
