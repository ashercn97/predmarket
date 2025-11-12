from __future__ import annotations
from yarl import URL
from predmarket.core.models import Question, Contract, Platform
from predmarket.model.rest import (
    Response,
    BaseExchangeClient,
    clean_params,
)


class KalshiRest(BaseExchangeClient):
    """Kalshi-specific implementation."""

    BASE_URL = URL("https://api.elections.kalshi.com/trade-api/v2/")

    async def fetch_contracts(self, **kwargs) -> Response[list[Contract]]:
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        contracts = [
            Contract(
                id=market.get("ticker"),
                platform=Platform.KALSHI,
                question_id=market.get("event_ticker"),
                outcomes=["Yes", "No"],
                raw=market,
            )
            for market in data.get("markets", [])
        ]
        return Response(
            data=contracts,
            metadata={"cursor": data.get("cursor")},
        )

    async def fetch_questions(self, **kwargs) -> Response[list[Question]]:
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        questions = [
            Question(
                id=event.get("event_ticker"),
                platform=Platform.KALSHI,
                title=event.get("title"),
                raw=event,
            )
            for event in data.get("events", [])
        ]
        return Response(
            data=questions,
            metadata={"cursor": data.get("cursor")},
        )
