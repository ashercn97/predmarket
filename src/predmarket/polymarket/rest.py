import json
from collections.abc import AsyncIterator
from typing import Any

from yarl import URL

from predmarket.errors import PredmarketError
from predmarket.model.rest import (
    BaseExchangeClient,
    Contract,
    OrderBook,
    Price,
    Question,
    Response,
    clean_params,
)


class PolymarketRest(BaseExchangeClient):
    """Polymarket-specific implementation.

    Metadata and events come from the Gamma API; order books come from the CLOB
    API, which is the authoritative source for resting depth.
    """

    BASE_URL = URL("https://gamma-api.polymarket.com/")
    CLOB_URL = URL("https://clob.polymarket.com/")
    # Gamma ignores a larger limit and returns at most this many records.
    PAGE_LIMIT = 100

    async def fetch_price(self, id: str) -> Response[Price]:
        self.log.debug("fetch_price id=%s", id)

        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Price.from_polymarket(data), metadata={})

    async def fetch_orderbook(self, id: str) -> Response[OrderBook]:
        """Fetch depth for a market's primary outcome token."""
        self.log.debug("fetch_orderbook id=%s", id)

        market = await self._safe_get(self.BASE_URL / "markets" / id, {})
        token = self._primary_token(id, market)
        data = await self._safe_get(self.CLOB_URL / "book", {"token_id": token})
        return Response(
            data=OrderBook.from_polymarket(id, data),
            metadata={"token_id": token},
        )

    @staticmethod
    def _primary_token(id: str, market: dict[str, Any]) -> str:
        tokens = market.get("clobTokenIds")
        if isinstance(tokens, str):
            tokens = json.loads(tokens)
        if not tokens:
            raise PredmarketError(f"Polymarket market {id} exposes no clobTokenIds")
        return tokens[0]

    async def fetch_contract(self, id: str) -> Response[Contract]:
        self.log.debug("fetch_contract id=%s", id)

        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Contract.from_polymarket(data), metadata={})

    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        self.log.debug("fetch_contracts query=%s", kwargs)
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        return Response(
            data=[Contract.from_polymarket(m) for m in data],
            metadata={},
        )

    async def fetch_question(self, id: str) -> Response[Question]:
        self.log.debug("fetch_question id=%s", id)
        data = await self._safe_get(self.BASE_URL / "events" / id, {})
        return Response(data=Question.from_polymarket(data), metadata={})

    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        self.log.debug("fetch_questions query=%s", kwargs)
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        return Response(
            data=[Question.from_polymarket(event) for event in data],
            metadata={},
        )

    async def iter_contracts(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Contract]:
        """Walk every matching contract, paging with ``offset``."""
        size = min(page_size or self.PAGE_LIMIT, self.PAGE_LIMIT)
        offset = int(kwargs.pop("offset", 0) or 0)

        while True:
            page = await self.fetch_contracts(limit=size, offset=offset, **kwargs)
            if not page.data:
                return
            for contract in page.data:
                yield contract
            if len(page.data) < size:
                return
            offset += size

    async def iter_questions(
        self, *, page_size: int | None = None, **kwargs: Any
    ) -> AsyncIterator[Question]:
        """Walk every matching question, paging with ``offset``."""
        size = min(page_size or self.PAGE_LIMIT, self.PAGE_LIMIT)
        offset = int(kwargs.pop("offset", 0) or 0)

        while True:
            page = await self.fetch_questions(limit=size, offset=offset, **kwargs)
            if not page.data:
                return
            for question in page.data:
                yield question
            if len(page.data) < size:
                return
            offset += size
