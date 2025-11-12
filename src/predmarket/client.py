from predmarket.kalshi.rest import KalshiRest
from predmarket.polymarket.rest import PolymarketRest
from predmarket.core.models import Question, Contract, Platform
from predmarket.model.rest import Response
from typing import Any
import asyncio

class UnifiedClient:
    def __init__(self, kalshi: KalshiRest, polymarket: PolymarketRest):
        self.kalshi = kalshi
        self.polymarket = polymarket

    async def fetch_questions(self, **kwargs: Any) -> list[Question]:
        kalshi_questions_task = self.kalshi.fetch_questions(**kwargs)
        polymarket_questions_task = self.polymarket.fetch_questions(**kwargs)

        kalshi_response, polymarket_response = await asyncio.gather(
            kalshi_questions_task,
            polymarket_questions_task
        )

        return kalshi_response.data + polymarket_response.data

    async def fetch_contracts(self, **kwargs: Any) -> list[Contract]:
        kalshi_contracts_task = self.kalshi.fetch_contracts(**kwargs)
        polymarket_contracts_task = self.polymarket.fetch_contracts(**kwargs)

        kalshi_response, polymarket_response = await asyncio.gather(
            kalshi_contracts_task,
            polymarket_contracts_task
        )

        return kalshi_response.data + polymarket_response.data
