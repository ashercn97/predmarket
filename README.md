# A Unified SDK for Prediction Markets

### Check out [The Odds Company](https://github.com/orgs/the-odds-company/repositories) for similar projects

`predmarket` is an `asyncio`-native Python-based library that communicates directly with prediction markets (Kalshi and Polymarket).

Both Kalshi and Polymarket provide public-facing APIs with high rate limits. `predmarket` aims to unify these two APIs into one install, one format, and one library to learn. The goal to be abstract enough to be intuitive, but not lose **any** power of the individual APIs.

Currently, Websocket support is under development. A working implementation of Polymarket's CLOB WS API is available, while Kalshi's is still being developed.

## Install
```uv add predmarket ```
or
`pip install predmarket`

## Basic Usage

### REST
```python
from predmarket import UnifiedClient, KalshiRest, PolymarketRest
from httpx import AsyncClient
import asyncio

async def main():
    async with AsyncClient() as client:
        # Initialize fetchers for each platform
        kalshi = KalshiRest(client)
        polymarket = PolymarketRest(client)

        # Initialize the unified client
        unified_client = UnifiedClient(kalshi, polymarket)

        # Fetch available Questions (e.g. "When will Elon Musk get to Mars?")
        questions = await unified_client.fetch_questions()
        for question in questions:
            print(f"- {question.title} ({question.platform})")

        # Fetch available Contracts  (e.g. "Will Elon Musk get to Mars before 2026?")
        contracts = await unified_client.fetch_contracts()
        for contract in contracts:
            print(f"- {contract.id} ({contract.platform})")

if __name__ == "__main__":
    asyncio.run(main())
```
### WS
```python
from predmarket import PolymarketWS # Kalshi is NOT currently supported, but will be very solutions

async def main():
    async with PolymarketWS.connect() as socket:
        polymarket = PolymarketWS(socket)
        for row in polymarket.stream(["AB.....XYZ"]): # Example of fetching real markets later in docs
            print(row) # Row is a pydantic model. Autocomplete!


```
## More Information
`predmarket` is under rapid development. Expect breaking changes unless indiciated otherwise.
