from typing import Any

from pydantic import BaseModel, ConfigDict


def coerce_float(value: Any) -> float | None:
    """Best-effort float conversion that tolerates missing or malformed values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def kalshi_quote(market: dict[str, Any], field: str) -> float | None:
    """Read a Kalshi price.

    Kalshi quotes prices as decimal strings under ``*_dollars``; older payloads
    carried integer cents under the bare field name.
    """
    if (value := market.get(f"{field}_dollars")) is not None:
        return coerce_float(value)
    if (cents := coerce_float(market.get(field))) is None:
        return None
    return cents / 100


def kalshi_count(market: dict[str, Any], field: str) -> float | None:
    """Read a Kalshi contract count, which is exposed as a ``*_fp`` decimal string."""
    if (value := market.get(f"{field}_fp")) is not None:
        return coerce_float(value)
    return coerce_float(market.get(field))


class Price(BaseModel):
    """Normalized price of a contract."""

    model_config = ConfigDict(frozen=True)

    bid: float | None = None
    ask: float | None = None
    price: float | None = None
    volume: float | None = None
    liquidity: float | None = None

    @classmethod
    def from_kalshi(cls, market: dict[str, Any]) -> "Price":
        return cls(
            price=kalshi_quote(market, "last_price"),
            ask=kalshi_quote(market, "yes_ask"),
            bid=kalshi_quote(market, "yes_bid"),
            volume=kalshi_count(market, "volume"),
        )

    @classmethod
    def from_polymarket(cls, market: dict[str, Any]) -> "Price":
        return cls(
            price=coerce_float(market.get("lastTradePrice")),
            ask=coerce_float(market.get("bestAsk")),
            bid=coerce_float(market.get("bestBid")),
            volume=coerce_float(market.get("volume")),
            liquidity=coerce_float(market.get("liquidity")),
        )
