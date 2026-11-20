from typing import Any, Literal

from .contract import Contract
from .exchange import BaseExchangeClient
from .price import Price
from .question import Question
from .response import Response

type ExchangeName = Literal["polymarket", "kalshi"]


def clean_params(**kwargs: Any) -> dict[str, Any]:
    """Remove None values from kwargs before sending them as query params."""
    return {k: v for k, v in kwargs.items() if v is not None}


__all__ = [
    "BaseExchangeClient",
    "Contract",
    "ExchangeName",
    "Price",
    "Question",
    "Response",
    "clean_params",
]
