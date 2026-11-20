# A Unified SDK for Prediction Markets

`predmarket` is an `asyncio`-native Python library that talks directly to prediction markets (Kalshi and Polymarket).

Both Kalshi and Polymarket expose public APIs with high rate limits. `predmarket` unifies them into one install, one format, and one library to learn. It aims to be abstract enough to be intuitive, without giving up any power of the individual APIs.

REST support is complete for both exchanges. On the websocket side, Polymarket's CLOB market channel is implemented; Kalshi's websocket support is still in progress.

## Install

```sh
uv add predmarket
```

or

```sh
pip install predmarket
```

Requires Python 3.13 or newer.

## Basic Usage

### REST

```python
import asyncio

from httpx import AsyncClient

from predmarket import KalshiRest, PolymarketRest


async def main() -> None:
    async with AsyncClient() as client:
        # Each client exposes the same public API.
        kalshi = KalshiRest(client)
        polymarket = PolymarketRest(client)

        # Fetch available questions (events in the native APIs).
        kalshi_questions = await kalshi.fetch_questions()
        polymarket_questions = await polymarket.fetch_questions(limit=10, asc=True)

        # Fetch available contracts (markets in the native APIs).
        kalshi_contracts = await kalshi.fetch_contracts()
        polymarket_contracts = await polymarket.fetch_contracts()

        # Fetch a price for one contract.
        price = await kalshi.fetch_price("KXELONMARS-99")
        print(price.data.bid, price.data.ask, price.data.price)


asyncio.run(main())
```

Query parameters are passed straight through, so anything the native API accepts works here. `None` values are dropped before the request is sent.

### Websocket

```python
import asyncio

from predmarket import PolymarketWS


async def main() -> None:
    async with PolymarketWS.connect() as socket:
        stream = PolymarketWS(socket).stream(["<asset_id>"])
        async for update in stream:
            print(update.model_dump_json())


asyncio.run(main())
```

`stream` yields typed models — `BookSnapshot`, `BookDelta`, `Trade`, or `Ticker` — so your editor autocompletes every field. See [`examples/stream_polymarket.py`](examples/stream_polymarket.py) for a runnable version that streams the busiest live markets.

### Errors

Failures raise subclasses of `PredmarketError`, importable from `predmarket` or `predmarket.errors`: `APIError` when an exchange answers with a non-success status (it carries `status_code` and `body`), and `TransportError` when the request never produced a response.

## Development

```sh
uv sync
uv run ruff check .
uv run python examples/stream_polymarket.py
```

## More Information

`predmarket` is under rapid development. Expect breaking changes unless indicated otherwise.
