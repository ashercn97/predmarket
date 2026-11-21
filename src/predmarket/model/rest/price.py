from typing import Any

from pydantic import BaseModel, ConfigDict

from .._parse import coerce_float, kalshi_count, kalshi_dollars

__all__ = ["Price", "coerce_float"]


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
            price=kalshi_dollars(market, "last_price"),
            ask=kalshi_dollars(market, "yes_ask"),
            bid=kalshi_dollars(market, "yes_bid"),
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
