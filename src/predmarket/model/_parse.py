"""Shared coercion helpers for exchange payloads."""

from datetime import UTC, datetime
from typing import Any


def coerce_float(value: Any) -> float | None:
    """Best-effort float conversion that tolerates missing or malformed values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def kalshi_dollars(market: dict[str, Any], field: str) -> float | None:
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
    """Read a Kalshi contract count, exposed as a ``*_fp`` decimal string."""
    if (value := market.get(f"{field}_fp")) is not None:
        return coerce_float(value)
    return coerce_float(market.get(field))


def levels_from_pairs(raw: Any, *, cents: bool = False) -> list[tuple[float, float]]:
    """Normalize ``[[price, size], ...]`` into price/size float pairs.

    Kalshi sends decimals in dollars as strings; older payloads sent prices as
    integer cents, which ``cents=True`` divides down.
    """
    if not isinstance(raw, list):
        return []

    pairs: list[tuple[float, float]] = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        price = coerce_float(row[0])
        size = coerce_float(row[1])
        if price is None or size is None:
            continue
        pairs.append((price / 100 if cents else price, size))
    return pairs


def epoch_ms(value: Any) -> datetime | None:
    """Convert a millisecond epoch timestamp into an aware datetime."""
    ms = coerce_float(value)
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


def iso_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
