from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

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


def _epoch_ms(value: Any) -> datetime | None:
    """Convert a millisecond epoch timestamp into an aware datetime."""
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def _iso(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class PolymarketParser:
    """Parse Polymarket CLOB websocket messages into unified models."""

    @staticmethod
    def parse(msg: dict[str, Any]) -> UnifiedModel | None:
        timestamp = _epoch_ms(msg.get("timestamp"))
        market_id = msg.get("market") or msg.get("condition_id") or msg.get("asset_id") or ""

        match msg.get("event_type"):
            case "book":
                return BookSnapshot(
                    exchange=Exchange.POLYMARKET,
                    market_id=market_id,
                    bids=[
                        PriceLevel(price=float(x["price"]), size=float(x["size"]), side=Side.BUY)
                        for x in msg.get("bids", [])
                    ],
                    asks=[
                        PriceLevel(price=float(x["price"]), size=float(x["size"]), side=Side.SELL)
                        for x in msg.get("asks", [])
                    ],
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
                    ],
                    timestamp=timestamp,
                )
            case "last_trade_price":
                return Trade(
                    exchange=Exchange.POLYMARKET,
                    market_id=market_id,
                    price=float(msg.get("price", 0)),
                    size=float(msg.get("size", 0)),
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
        timestamp = _iso(data.get("ts"))
        market_id = data.get("market_ticker") or ""

        match msg.get("type"):
            case "orderbook_snapshot":
                return BookSnapshot(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    bids=[
                        PriceLevel(price=price / 100, size=size, side=Side.YES)
                        for price, size in data.get("yes", [])
                    ],
                    asks=[
                        PriceLevel(price=price / 100, size=size, side=Side.NO)
                        for price, size in data.get("no", [])
                    ],
                    timestamp=timestamp,
                )
            case "orderbook_delta":
                return BookDelta(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    deltas=[
                        PriceLevel(
                            price=price / 100,
                            size=size,
                            side=Side.YES if side == "yes" else Side.NO,
                        )
                        for side in ("yes", "no")
                        for price, size in data.get(side, [])
                    ],
                    timestamp=timestamp,
                )
            case "trade":
                taker = Side.YES if data.get("taker_side") == "yes" else Side.NO
                return Trade(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    price=float(data.get("yes_price", 0)) / 100,
                    size=float(data.get("count", 0)),
                    side=taker,
                    taker_side=taker,
                    timestamp=timestamp,
                )
            case "ticker":
                return Ticker(
                    exchange=Exchange.KALSHI,
                    market_id=market_id,
                    last_price=data["price"] / 100 if data.get("price") else None,
                    best_bid=data["yes_bid"] / 100 if data.get("yes_bid") else None,
                    best_ask=data["yes_ask"] / 100 if data.get("yes_ask") else None,
                    volume=float(data["volume"]) if data.get("volume") else None,
                    open_interest=float(data["open_interest"])
                    if data.get("open_interest")
                    else None,
                    timestamp=timestamp,
                )
            case _:
                return None


def normalize_message(msg: dict[str, Any], source: Exchange | str) -> UnifiedModel | None:
    """Normalize a raw exchange websocket message into a unified model."""
    match source:
        case Exchange.POLYMARKET | "polymarket":
            return PolymarketParser.parse(msg)
        case Exchange.KALSHI | "kalshi":
            return KalshiParser.parse(msg)
        case _:
            raise ValueError(f"Unknown source: {source}")
