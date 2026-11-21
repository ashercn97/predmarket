from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = ["Question"]


class Question(BaseModel):
    """Normalized event/question across exchanges."""

    model_config = ConfigDict(extra="allow")

    id: str
    platform: str
    title: str | None = None
    raw: dict[str, Any]

    @classmethod
    def from_polymarket(cls, event: dict[str, Any]) -> "Question":
        return cls.model_validate(
            {
                **event,
                "id": event.get("id"),
                "platform": "polymarket",
                "title": event.get("title") or event.get("question"),
                "raw": event,
            }
        )

    @classmethod
    def from_kalshi(cls, event: dict[str, Any]) -> "Question":
        return cls.model_validate(
            {
                **event,
                "id": event.get("event_ticker"),
                "platform": "kalshi",
                "title": event.get("title"),
                "raw": event,
            }
        )
