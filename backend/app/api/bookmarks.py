from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bookmark import Bookmark
from app.models.ruling import Ruling
from app.models.user import User
from app.schemas.ruling import RulingListItem
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[RulingListItem])
async def list_bookmarks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bookmarked rulings for the current user."""
    result = await db.execute(
        select(Ruling)
        .join(Bookmark, Bookmark.ruling_id == Ruling.id)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
    )
    rulings = result.scalars().all()
    return rulings


@router.post("/{ruling_id}", status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    ruling_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a ruling."""
    # Check ruling exists
    result = await db.execute(select(Ruling).where(Ruling.id == ruling_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบคำพิพากษาฎีกา",
        )

    # Check if already bookmarked
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == user.id, Bookmark.ruling_id == ruling_id
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="บันทึกฎีกานี้ไว้แล้ว",
        )

    bookmark = Bookmark(user_id=user.id, ruling_id=ruling_id)
    db.add(bookmark)
    await db.commit()
    return {"detail": "บันทึกฎีกาเรียบร้อย"}


@router.delete("/{ruling_id}", status_code=status.HTTP_200_OK)
async def remove_bookmark(
    ruling_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark."""
    result = await db.execute(
        delete(Bookmark).where(
            Bookmark.user_id == user.id, Bookmark.ruling_id == ruling_id
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบบุ๊คมาร์ค",
        )
    await db.commit()
    return {"detail": "ลบบุ๊คมาร์คเรียบร้อย"}
