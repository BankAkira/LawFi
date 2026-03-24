from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "ruling_id", name="uq_user_ruling"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ruling_id: Mapped[int] = mapped_column(ForeignKey("rulings.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
