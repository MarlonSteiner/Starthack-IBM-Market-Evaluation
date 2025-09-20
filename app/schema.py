from pydantic import BaseModel, Field
from typing import List, Optional

class NewsItem(BaseModel):
    id: str
    published_at: str
    source: str
    url: str
    headline: str
    body_text: str = ""
    tickers: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    event_type: Optional[str] = None
    regions: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    urgency: Optional[str] = None
    why_it_matters: Optional[str] = None
    draft_note: Optional[str] = None
    hash: str
