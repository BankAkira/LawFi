import enum
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"
    LINE = "line"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    auth_provider: Mapped[AuthProvider] = mapped_column(default=AuthProvider.EMAIL)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        default=SubscriptionTier.FREE
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    daily_search_count: Mapped[int] = mapped_column(default=0)
    last_search_date: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
