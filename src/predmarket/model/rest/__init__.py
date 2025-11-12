from __future__ import annotations
from typing import Any, Literal
from .exchange import *
ExchangeName = Literal["polymarket", "kalshi"]


def clean_params(**kwargs: Any) -> dict[str, Any]:
    """Remove None values from kwargs before sending as query params."""
    return {k: v for k, v in kwargs.items() if v is not None}


__all__ = [
    "Response",
    "BaseExchangeClient",
    "clean_params",
]
