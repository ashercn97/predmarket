from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from .._parse import coerce_float, epoch_ms, iso_timestamp, levels_from_pairs
from ..book import PriceLevel, Side

__all__ = [
    "BookDelta",
    "BookSnapshot",
    "Exchange",
    "KalshiParser",
    "PolymarketParser",
    "PriceLevel",
    "Side",
    "Ticker",
    "Trade",
    "UnifiedModel",
    "normalize_message",
]


class Exchange(StrEnum):
    """Exchanges predmarket speaks to."""

    POLYMARKET = "polymarket"
    KALSHI = "kalshi"


class BookSnapshot(BaseModel):
    """Full order book for a market."""

    exchange: Exchange
    market_id: str
    bids: list[PriceLevel]
    asks: list[PriceLevel]
    timestamp: datetime | None = None


class BookDelta(BaseModel):
    """Incremental change to an order book."""

    exchange: Exchange
    market_id: str
    deltas: list[PriceLevel]
    timestamp: datetime | None = None


class Trade(BaseModel):
    """A completed trade."""

    exchange: Exchange
    market_id: str
    price: float
    size: float
    side: Side
    taker_side: Side | None = None
    timestamp: datetime | None = None


class Ticker(BaseModel):
    """Best bid/offer and volume summary for a market."""

    exchange: Exchange
    market_id: str
    last_price: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    volume: float | None = None
    open_interest: float | None = None
    timestamp: datetime | None = None


type UnifiedModel = BookSnapshot | BookDelta | Trade | Ticker


def _polymarket_levels(raw: Any, side: Side) -> list[PriceLevel]:
    """Polymarket book levels carry ``price``/``size`` as decimal strings."""
    return [
        PriceLevel(price=float(level["price"]), size=float(level["size"]), side=side)
        for level in raw or []
        if isinstance(level, dict) and "price" in level and "size" in level
    ]


def _kalshi_side(data: dict[str, Any], side: str) -> list[tuple[float, float]]:
    """Kalshi lists each side as ``[[price, size], ...]`` in dollars."""
    modern = f"{side}_dollars"
    if modern in data:
        return levels_from_pairs(data.get(modern))
    return levels_from_pairs(data.get(side), cents=True)


class PolymarketParser:
    """Parse Polymarket CLOB websocket messages into unified models."""

    @staticmethod
    def parse(msg: dict[str, Any]) -> UnifiedModel | None:
        timestamp = epoch_ms(msg.get("timestamp"))
        market_id = msg.get("market") or msg.get("condition_id") or msg.get("asset_id") or ""

        match msg.get("event_type"):
            case "book":
                return BookSnapshot(
                    exchange=Exchange.POLYMARKET,
                    market_id=market_id,
                    bids=_polymarket_levels(msg.get("bids"), Side.BUY),
                    asks=_polymarket_levels(msg.get("asks"), Side.SELL),
                    timestamp=timestamp,
                )
            case "price_change":
                return BookDelta(
                    exchange=Exchange.POLYMARKET,
                    market_id=market_id,
                    deltas=[
                        PriceLevel(
                            price=float(change["price"]),
                            size=float(change["size"]),
                            side=Side.BUY if change.get("side") == "BUY" else Side.SELL,
                        )
                        for change in msg.get("price_changes", [])
                        if "price" in change and "size" in change
                    ],
                    timestamp=timestamp,
                )
            case "last_trade_price":
                return Trade(
                    exchange=Exchange.POLYMARKET,
                    market_id=market_id,
                    price=coerce_float(msg.get("price")) or 0.0,
                    size=coerce_float(msg.get("size")) or 0.0,
                    side=Side.BUY if msg.get("side") == "BUY" else Side.SELL,
                    timestamp=timestamp,
                )
            case _:
                return None


class KalshiParser:
    """Parse Kalshi websocket messages into unified models."""

    @staticmethod
    def parse(msg: dict[str, Any]) -> UnifiedModel | None:
        data = msg.get("msg") or msg.get("data") or {}
        timestamp = iso_timestamp(data.get("ts"))
        market_id = data.get("market_ticker") or ""

        match msg.get("type"):
            case "orderbook_snapshot":
                return BookSnapshot(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    bids=[
                        PriceLevel(price=price, size=size, side=Side.YES)
                        for price, size in sorted(_kalshi_side(data, "yes"), reverse=True)
                    ],
                    asks=[
                        PriceLevel(price=round(1 - price, 6), size=size, side=Side.YES)
                        for price, size in sorted(_kalshi_side(data, "no"), reverse=True)
                    ],
                    timestamp=timestamp,
                )
            case "orderbook_delta":
                return BookDelta(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    deltas=[
                        PriceLevel(
                            price=price if side == "yes" else round(1 - price, 6),
                            size=size,
                            side=Side.YES,
                        )
                        for side in ("yes", "no")
                        for price, size in _kalshi_side(data, side)
                    ],
                    timestamp=timestamp,
                )
            case "trade":
                taker = Side.YES if data.get("taker_side") == "yes" else Side.NO
                return Trade(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    price=(coerce_float(data.get("yes_price_dollars")) or 0.0),
                    size=coerce_float(data.get("count")) or 0.0,
                    side=taker,
                    taker_side=taker,
                    timestamp=timestamp,
                )
            case "ticker":
                return Ticker(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    last_price=coerce_float(data.get("price_dollars")),
                    best_bid=coerce_float(data.get("yes_bid_dollars")),
                    best_ask=coerce_float(data.get("yes_ask_dollars")),
                    volume=coerce_float(data.get("volume")),
                    open_interest=coerce_float(data.get("open_interest")),
                    timestamp=timestamp,
                )
            case _:
                return None


def normalize_message(msg: dict[str, Any], source: Exchange | str) -> UnifiedModel | None:
    """Normalize a raw exchange websocket message into a unified model."""
    match source:
        case "polymarket":
            return PolymarketParser.parse(msg)
        case "kalshi":
            return KalshiParser.parse(msg)
        case _:
            raise ValueError(f"Unknown source: {source}")
