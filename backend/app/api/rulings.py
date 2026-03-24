from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ruling import Ruling
from app.schemas.ruling import RulingDetail

router = APIRouter()


@router.get("/{ruling_id}", response_model=RulingDetail)
async def get_ruling(ruling_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific ruling."""
    result = await db.execute(select(Ruling).where(Ruling.id == ruling_id))
    ruling = result.scalar_one_or_none()

    if ruling is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบคำพิพากษาฎีกา",
        )

    return ruling


@router.get("/number/{ruling_number}", response_model=RulingDetail)
async def get_ruling_by_number(ruling_number: str, db: AsyncSession = Depends(get_db)):
    """Get ruling by its official number (e.g. '1234/2565')."""
    result = await db.execute(
        select(Ruling).where(Ruling.ruling_number == ruling_number)
    )
    ruling = result.scalar_one_or_none()

    if ruling is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ไม่พบฎีกาหมายเลข {ruling_number}",
        )

    return ruling
