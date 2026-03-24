from pydantic import BaseModel, Field

from app.models.ruling import CaseType, RulingResult
from app.schemas.ruling import RulingListItem


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    case_type: CaseType | None = None
    year_from: int | None = None
    year_to: int | None = None
    result: RulingResult | None = None
    keywords: list[str] | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    results: list[RulingListItem]
    total: int
    page: int
    page_size: int
    query: str
