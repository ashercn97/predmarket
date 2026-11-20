from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Self

from yarl import URL

from predmarket.errors import APIError, TransportError

from ..book import OrderBook
from .contract import Contract
from .price import Price
from .question import Question
from .response import Response

if TYPE_CHECKING:
    from httpx import AsyncClient

__all__ = ["BaseExchangeClient"]

RETRY_STATUS = frozenset({429, 500, 502, 503, 504})


class BaseExchangeClient(ABC):
    """Shared transport, retry, and pagination for exchange-specific clients.

    The client owns an ``httpx.AsyncClient`` when none is supplied, so it works
    standalone and as a context manager::

        async with PolymarketRest() as polymarket:
            contracts = await polymarket.fetch_contracts(limit=10)

    ``httpx`` is imported on first use, so ``import predmarket`` and the
    websocket path never pay for it.
    """

    PAGE_LIMIT: int = 100

    def __init__(
        self,
        client: AsyncClient | None = None,
        *,
        timeout: float = 30.0,
        retries: int = 2,
        backoff: float = 0.25,
    ) -> None:
        self._owns_client = client is None
        if client is None:
            import httpx

            client = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout),
                limits=httpx.Limits(max_connections=64, max_keepalive_connections=16),
            )
        self._client = client
        self._retries = retries
        self._backoff = backoff
        self.log = logging.getLogger(type(self).__module__)

    async def aclose(self) -> None:
        """Close the underlying HTTP client when this object created it."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def _get_once(self, url: URL, params: dict[str, Any]) -> Any:
        from httpx import HTTPStatusError, RequestError

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

    async def _safe_get(self, url: URL, params: dict[str, Any]) -> Any:
        """Perform a GET, retrying rate limits and transient server errors."""
        attempts = self._retries + 1
        for attempt in range(attempts):
            try:
                return await self._get_once(url, params)
            except (APIError, TransportError) as exc:
                retryable = not isinstance(exc, APIError) or exc.status_code in RETRY_STATUS
                if not retryable or attempt == attempts - 1:
                    raise
                delay = self._backoff * (2**attempt) + random.uniform(0, self._backoff)
                self.log.debug("retrying %s in %.2fs after %s", url, delay, exc)
                await asyncio.sleep(delay)
        raise AssertionError("unreachable")

    async def fetch_many(self, ids: list[str], *, concurrency: int = 8) -> list[Response[Contract]]:
        """Fetch several contracts concurrently, preserving input order."""
        semaphore = asyncio.Semaphore(concurrency)

        async def one(market_id: str) -> Response[Contract]:
            async with semaphore:
                return await self.fetch_contract(market_id)

        return list(await asyncio.gather(*(one(market_id) for market_id in ids)))

    @abstractmethod
    def iter_contracts(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Contract]:
        """Yield contracts across pages, following the exchange's own paging."""

    @abstractmethod
    def iter_questions(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Question]:
        """Yield questions across pages, following the exchange's own paging."""

    @abstractmethod
    async def fetch_price(self, id: str) -> Response[Price]:
        """Fetch a single contract price."""

    @abstractmethod
    async def fetch_orderbook(self, id: str) -> Response[OrderBook]:
        """Fetch resting order book depth for a single contract."""

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
