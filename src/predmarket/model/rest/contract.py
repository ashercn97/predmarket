import json
from typing import Any

from pydantic import BaseModel, ConfigDict

from .price import coerce_float

__all__ = ["Contract", "coerce_float"]


class Contract(BaseModel):
    """Normalized market contract."""

    model_config = ConfigDict(extra="allow")

    id: str
    platform: str
    question: str
    outcomes: list[str]
    raw: dict[str, Any]

    @property
    def price(self) -> float | None:
        """Last traded price, when the exchange reports one."""
        match self.platform:
            case "kalshi":
                return coerce_float(self.raw.get("last_price_dollars"))
            case "polymarket":
                return coerce_float(self.raw.get("lastTradePrice"))
            case _:
                return None

    @staticmethod
    def _normalize_outcomes(value: Any) -> list[str]:
        """Polymarket sometimes delivers outcomes as a JSON-encoded string."""
        match value:
            case list():
                return [str(item) for item in value]
            case str():
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    return [value]
                return [str(item) for item in parsed] if isinstance(parsed, list) else [value]
            case _:
                return []

    @classmethod
    def from_polymarket(cls, market: dict[str, Any]) -> "Contract":
        return cls.model_validate(
            {
                **market,
                "id": market.get("id"),
                "platform": "polymarket",
                "question": market.get("question"),
                "outcomes": cls._normalize_outcomes(market.get("outcomes")),
                "raw": market,
            }
        )

    @classmethod
    def from_kalshi(cls, market: dict[str, Any]) -> "Contract":
        return cls.model_validate(
            {
                **market,
                "id": market.get("ticker"),
                "platform": "kalshi",
                "question": market.get("title"),
                "outcomes": ["Yes", "No"],
                "raw": market,
            }
        )
