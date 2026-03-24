from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ruling import CaseType, RulingResult


class RulingListItem(BaseModel):
    """Brief ruling info for search results."""

    id: int
    ruling_number: str
    year: int
    case_type: CaseType | None
    result: RulingResult | None
    summary: str | None
    keywords: list[str] | None
    relevance_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class RulingDetail(BaseModel):
    """Full ruling details."""

    id: int
    ruling_number: str
    year: int
    date: datetime | None
    case_type: CaseType | None
    division: str | None
    result: RulingResult | None
    summary: str | None
    facts: str | None
    issues: str | None
    judgment: str | None
    full_text: str
    keywords: list[str] | None
    referenced_sections: list[str] | None
    pdf_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
