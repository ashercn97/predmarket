from abc import ABC, abstractmethod
from typing import Any

from httpx import AsyncClient, HTTPStatusError, RequestError
from yarl import URL

from predmarket.errors import APIError, TransportError

from .contract import Contract
from .price import Price
from .question import Question
from .response import Response

__all__ = ["BaseExchangeClient"]


class BaseExchangeClient(ABC):
    """Shared helpers for exchange-specific clients."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def _safe_get(self, url: URL, params: dict[str, Any]) -> Any:
        """Perform a GET request, raising a predmarket error on failure."""
        try:
            response = await self._client.get(str(url), params=params)
            response.raise_for_status()
        except HTTPStatusError as exc:
            raise APIError(str(url), exc.response.status_code, exc.response.text) from exc
        except RequestError as exc:
            raise TransportError(f"Request to {url} failed: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise APIError(str(url), response.status_code, response.text) from exc

    @abstractmethod
    async def fetch_price(self, id: str) -> Response[Price]:
        """Fetch a single contract price."""

    @abstractmethod
    async def fetch_contract(self, id: str) -> Response[Contract]:
        """Fetch metadata for a single contract."""

    @abstractmethod
    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        """Fetch a batch of contracts."""

    @abstractmethod
    async def fetch_question(self, id: str) -> Response[Question]:
        """Fetch metadata for a single question/event."""

    @abstractmethod
    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        """Fetch a batch of questions/events."""
