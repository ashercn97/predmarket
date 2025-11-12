from pydantic import BaseModel, Field
from enum import Enum
from typing import Any

class Platform(str, Enum):
    POLIMARKET = "polymarket"
    KALSHI = "kalshi"

class Question(BaseModel):
    """Normalized event/question across exchanges."""

    id: str
    platform: Platform
    title: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

class Contract(BaseModel):
    """Normalized market contract."""

    id: str
    platform: Platform
    question_id: str
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)
    outcomes: list[str] = Field(default_factory=list)
