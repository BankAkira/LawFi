import enum
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaseType(str, enum.Enum):
    CIVIL = "แพ่ง"
    CRIMINAL = "อาญา"
    LABOR = "แรงงาน"
    TAX = "ภาษี"
    INTELLECTUAL_PROPERTY = "ทรัพย์สินทางปัญญา"
    BANKRUPTCY = "ล้มละลาย"
    ADMINISTRATIVE = "ปกครอง"
    FAMILY = "ครอบครัว"
    JUVENILE = "เยาวชน"
    ENVIRONMENTAL = "สิ่งแวดล้อม"
    OTHER = "อื่นๆ"


class RulingResult(str, enum.Enum):
    UPHELD = "ยืน"
    REVERSED = "กลับ"
    MODIFIED = "แก้"
    DISMISSED = "ยกฟ้อง"
    APPEAL_DISMISSED = "ยกอุทธรณ์"
    APPEAL_REVERSED = "กลับอุทธรณ์"
    OTHER = "อื่นๆ"


class Ruling(Base):
    __tablename__ = "rulings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ruling_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )  # e.g. "1234/2565"
    year: Mapped[int] = mapped_column(index=True)  # พ.ศ.
    date: Mapped[datetime | None] = mapped_column()
    case_type: Mapped[CaseType | None] = mapped_column(index=True)
    division: Mapped[str | None] = mapped_column(String(100))  # แผนก
    result: Mapped[RulingResult | None] = mapped_column(index=True)

    # Content sections (extracted by Claude)
    summary: Mapped[str | None] = mapped_column(Text)
    facts: Mapped[str | None] = mapped_column(Text)
    issues: Mapped[str | None] = mapped_column(Text)
    judgment: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str] = mapped_column(Text)

    # Metadata
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    referenced_sections: Mapped[list[str] | None] = mapped_column(
        ARRAY(String)
    )  # e.g. ["ป.พ.พ. มาตรา 420", "ป.อ. มาตรา 157"]

    # Storage references
    pdf_url: Mapped[str | None] = mapped_column(String(500))
    qdrant_id: Mapped[str | None] = mapped_column(
        String(100), index=True
    )  # UUID in Qdrant

    # Processing status
    is_processed: Mapped[bool] = mapped_column(default=False, index=True)
    processing_error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
