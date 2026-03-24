from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    search_type: Mapped[str] = mapped_column(
        String(20)
    )  # "keyword", "semantic", "hybrid"
    results_count: Mapped[int] = mapped_column(default=0)
    filters_applied: Mapped[str | None] = mapped_column(Text)  # JSON string
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
