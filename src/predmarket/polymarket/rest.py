from predmarket.core.models import Question, Contract, Platform
from predmarket.model.rest import (
    Response,
    BaseExchangeClient,
    clean_params,
)
from typing import Any
from yarl import URL
import structlog
import json

log = structlog.get_logger()


class PolymarketRest(BaseExchangeClient):
    BASE_URL = URL("https://gamma-api.polymarket.com/")
    log = log.bind(exchange="polymarket")

    def _normalize_outcomes(self, value: Any) -> list[str]:
        """Polymarket sometimes delivers outcomes as JSON strings."""
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return [value]
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [value]
        return []

    async def fetch_contracts(self, **kwargs: Any) -> Response[list[Contract]]:
        self.log.debug(query=kwargs, event="fetch_contracts")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "markets", params)
        contracts = [
            Contract(
                id=market.get("id"),
                platform=Platform.POLIMARKET,
                question_id=market.get("question_id"),
                outcomes=self._normalize_outcomes(market.get("outcomes")),
                raw=market,
            )
            for market in data
        ]
        return Response(
            data=contracts,
            metadata={},
        )

    async def fetch_questions(self, **kwargs: Any) -> Response[list[Question]]:
        self.log.debug(query=kwargs, event="fetch_questions")
        params = clean_params(**kwargs)
        data = await self._safe_get(self.BASE_URL / "events", params)
        questions = [
            Question(
                id=event.get("id"),
                platform=Platform.POLIMARKET,
                title=event.get("title") or event.get("question"),
                raw=event,
            )
            for event in data
        ]
        return Response(
            data=questions,
            metadata={},
        )
