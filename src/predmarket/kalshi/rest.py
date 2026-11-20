from collections.abc import AsyncIterator
from typing import Any

from yarl import URL

from predmarket.model.rest import (
    BaseExchangeClient,
    Contract,
    OrderBook,
    Price,
    Question,
    Response,
    clean_params,
)


class KalshiRest(BaseExchangeClient):
    """Kalshi-specific implementation."""

    BASE_URL = URL("https://api.elections.kalshi.com/trade-api/v2/")
    PAGE_LIMIT = 1000

    async def fetch_price(self, id: str) -> Response[Price]:
        self.log.debug("fetch_price id=%s", id)
        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Price.from_kalshi(data["market"]), metadata={})

    async def fetch_orderbook(self, id: str) -> Response[OrderBook]:
        self.log.debug("fetch_orderbook id=%s", id)
        data = await self._safe_get(self.BASE_URL / "markets" / id / "orderbook", {})
        return Response(data=OrderBook.from_kalshi(id, data), metadata={})

    async def fetch_contract(self, id: str) -> Response[Contract]:
        self.log.debug("fetch_contract id=%s", id)
        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Contract.from_kalshi(data["market"]), metadata={})

    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        self.log.debug("fetch_contracts query=%s", kwargs)
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        return Response(
            data=[Contract.from_kalshi(m) for m in data.get("markets", [])],
            metadata={"cursor": data.get("cursor")},
        )

    async def fetch_question(self, id: str) -> Response[Question]:
        self.log.debug("fetch_question id=%s", id)
        data = await self._safe_get(self.BASE_URL / "events" / id, {})
        return Response(data=Question.from_kalshi(data["event"]), metadata={})

    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        self.log.debug("fetch_questions query=%s", kwargs)
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        return Response(
            data=[Question.from_kalshi(event) for event in data.get("events", [])],
            metadata={"cursor": data.get("cursor")},
        )

    async def iter_contracts(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Contract]:
        """Walk every matching contract, following Kalshi's cursor."""
        size = min(page_size or self.PAGE_LIMIT, self.PAGE_LIMIT)
        cursor = kwargs.pop("cursor", None)

        while True:
            page = await self.fetch_contracts(limit=size, cursor=cursor, **kwargs)
            if not page.data:
                return
            for contract in page.data:
                yield contract
            cursor = page.metadata.get("cursor")
            if not cursor or len(page.data) < size:
                return

    async def iter_questions(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Question]:
        """Walk every matching question, following Kalshi's cursor."""
        size = min(page_size or self.PAGE_LIMIT, self.PAGE_LIMIT)
        cursor = kwargs.pop("cursor", None)

        while True:
            page = await self.fetch_questions(limit=size, cursor=cursor, **kwargs)
            if not page.data:
                return
            for question in page.data:
                yield question
            cursor = page.metadata.get("cursor")
            if not cursor or len(page.data) < size:
                return
