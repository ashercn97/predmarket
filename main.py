from predmarket.client import UnifiedClient
from predmarket.kalshi.rest import KalshiRest
from predmarket.polymarket.rest import PolymarketRest
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        kalshi = KalshiRest(client)
        polymarket = PolymarketRest(client)
        unified_client = UnifiedClient(kalshi, polymarket)

        print("--- Fetching questions ---")
        questions = await unified_client.fetch_questions()
        for question in questions:
            print(f"- {question.title} ({question.platform})")

        print("\n--- Fetching contracts ---")
        contracts = await unified_client.fetch_contracts()
        for contract in contracts:
            print(f"- {contract.id} ({contract.platform})")

if __name__ == "__main__":
    asyncio.run(main())
