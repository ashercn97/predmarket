from typing import Any

import structlog
from yarl import URL

from predmarket.model.rest import (
    BaseExchangeClient,
    Contract,
    Price,
    Question,
    Response,
    clean_params,
)

log = structlog.get_logger()


class PolymarketRest(BaseExchangeClient):
    BASE_URL = URL("https://gamma-api.polymarket.com/")
    log = log.bind(exchange="polymarket")

    async def fetch_price(self, id: str) -> Response[Price]:
        self.log.debug(id=id, event="fetch_price")

        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Price.from_polymarket(data), metadata={})

    async def fetch_contract(self, id: str) -> Response[Contract]:
        self.log.debug(id=id, event="fetch_contract")

        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Contract.from_polymarket(data), metadata={})

    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        self.log.debug(query=kwargs, event="fetch_contracts")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        return Response(
            data=[Contract.from_polymarket(m) for m in data],
            metadata={},
        )

    async def fetch_question(self, id: str) -> Response[Question]:
        self.log.debug(id=id, event="fetch_question")
        data = await self._safe_get(self.BASE_URL / "events" / id, {})
        return Response(data=Question.from_polymarket(data), metadata={})

    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        self.log.debug(query=kwargs, event="fetch_questions")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        return Response(
            data=[Question.from_polymarket(event) for event in data],
            metadata={},
        )
