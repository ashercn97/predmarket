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


class KalshiRest(BaseExchangeClient):
    """Kalshi-specific implementation."""

    BASE_URL = URL("https://api.elections.kalshi.com/trade-api/v2/")
    log = log.bind(exchange="kalshi")

    async def fetch_price(self, id: str) -> Response[Price]:
        self.log.debug(id=id, event="fetch_price")
        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Price.from_kalshi(data["market"]), metadata={})

    async def fetch_contract(self, id: str) -> Response[Contract]:
        self.log.debug(id=id, event="fetch_contract")
        data = await self._safe_get(self.BASE_URL / "markets" / id, {})
        return Response(data=Contract.from_kalshi(data["market"]), metadata={})

    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        self.log.debug(query=kwargs, event="fetch_contracts")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        return Response(
            data=[Contract.from_kalshi(m) for m in data.get("markets", [])],
            metadata={"cursor": data.get("cursor")},
        )

    async def fetch_question(self, id: str) -> Response[Question]:
        self.log.debug(id=id, event="fetch_question")
        data = await self._safe_get(self.BASE_URL / "events" / id, {})
        return Response(data=Question.from_kalshi(data["event"]), metadata={})

    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        self.log.debug(query=kwargs, event="fetch_questions")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        return Response(
            data=[Question.from_kalshi(event) for event in data.get("events", [])],
            metadata={"cursor": data.get("cursor")},
        )
