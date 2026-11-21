from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from ._parse import epoch_ms, kalshi_dollars, levels_from_pairs

__all__ = ["OrderBook", "PriceLevel", "Side"]


class Side(StrEnum):
    """Order side or contract outcome, depending on the model."""

    BUY = "buy"
    SELL = "sell"
    YES = "yes"
    NO = "no"


class PriceLevel(BaseModel):
    """One price level in an order book."""

    price: float
    size: float
    side: Side | None = None


class OrderBook(BaseModel):
    """Resting depth for one market, oriented on the ``Yes`` outcome.

    Both exchanges are normalized to one direction so books are comparable:
    ``bids`` are what buyers of ``Yes`` will pay, ``asks`` what sellers of
    ``Yes`` will take.
    """

    platform: str
    market_id: str
    bids: list[PriceLevel]
    asks: list[PriceLevel]
    timestamp: datetime | None = None

    @property
    def best_bid(self) -> float | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> float | None:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> float | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    @classmethod
    def from_kalshi(cls, ticker: str, payload: dict[str, Any]) -> "OrderBook":
        """Build a Yes-oriented book from Kalshi's ``orderbook_fp`` payload.

        Kalshi lists resting bids for each side separately. A bid of ``p`` on
        ``No`` is an offer of ``1 - p`` on ``Yes``, so the ``No`` side becomes
        the ask side.
        """
        book = payload.get("orderbook_fp") or payload.get("orderbook") or {}
        modern = "yes_dollars" in book or "no_dollars" in book

        yes = levels_from_pairs(book.get("yes_dollars" if modern else "yes"), cents=not modern)
        no = levels_from_pairs(book.get("no_dollars" if modern else "no"), cents=not modern)

        return cls(
            platform="kalshi",
            market_id=ticker,
            bids=[
                PriceLevel(price=price, size=size, side=Side.YES)
                for price, size in sorted(yes, reverse=True)
            ],
            asks=[
                PriceLevel(price=round(1 - price, 6), size=size, side=Side.YES)
                for price, size in sorted(no, reverse=True)
            ],
        )

    @classmethod
    def from_polymarket(cls, market_id: str, payload: dict[str, Any]) -> "OrderBook":
        """Build a book from Polymarket's CLOB ``/book`` payload for one token."""

        def levels(key: str, side: Side) -> list[PriceLevel]:
            parsed = [
                PriceLevel(price=float(level["price"]), size=float(level["size"]), side=side)
                for level in payload.get(key, [])
                if "price" in level and "size" in level
            ]
            return sorted(
                parsed,
                key=lambda level: level.price,
                reverse=side is Side.BUY,
            )

        return cls(
            platform="polymarket",
            market_id=market_id,
            bids=levels("bids", Side.BUY),
            asks=levels("asks", Side.SELL),
            timestamp=epoch_ms(payload.get("timestamp")),
        )

    @classmethod
    def from_kalshi_quote(cls, ticker: str, market: dict[str, Any]) -> "OrderBook":
        """Build a top-of-book view from Kalshi's single-market quote fields."""
        bid = kalshi_dollars(market, "yes_bid")
        ask = kalshi_dollars(market, "yes_ask")
        return cls(
            platform="kalshi",
            market_id=ticker,
            bids=[PriceLevel(price=bid, size=0.0, side=Side.YES)] if bid is not None else [],
            asks=[PriceLevel(price=ask, size=0.0, side=Side.YES)] if ask is not None else [],
        )
