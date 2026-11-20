# A Unified SDK for Prediction Markets

`predmarket` is an `asyncio`-native Python library that talks directly to prediction markets (Kalshi and Polymarket).

Both Kalshi and Polymarket expose public APIs with high rate limits. `predmarket` unifies them into one install, one format, and one library to learn. It aims to be abstract enough to be intuitive, without giving up any power of the individual APIs.

## Install

```sh
uv add predmarket
```

or

```sh
pip install predmarket
```

Requires Python 3.13 or newer. Dependencies are `httpx`, `pydantic`, and `websockets`; `httpx` is imported lazily, so `import predmarket` and the websocket path never load it.

## Quickstart

```python
import asyncio

from predmarket import KalshiRest, PolymarketRest


async def main() -> None:
    # Clients create and own their HTTP connection pool.
    async with PolymarketRest() as polymarket, KalshiRest() as kalshi:
        contracts = await polymarket.fetch_contracts(limit=10, closed=False)
        for contract in contracts.data:
            print(contract.id, contract.question, contract.price)

        # Order books are normalized to the same Yes-outcome orientation.
        book = await polymarket.fetch_orderbook(contracts[0].id)
        print(book.data.best_bid, book.data.best_ask, book.data.spread)

        price = await kalshi.fetch_price("KXELONMARS-99")
        print(price.data.bid, price.data.ask, price.data.price)


asyncio.run(main())
```

Pass your own client when you want to share a pool: `PolymarketRest(httpx.AsyncClient(...))`.

## What each exchange supports

Both clients expose the same surface, backed by the exchange's current API:

| Method | Polymarket source | Kalshi source |
| --- | --- | --- |
| `fetch_contracts` / `fetch_contract` | Gamma `/markets` | `/markets` |
| `fetch_questions` / `fetch_question` | Gamma `/events` | `/events` |
| `fetch_price` | Gamma `/markets/{id}` | `/markets/{id}` |
| `fetch_orderbook` | CLOB `/book` | `/markets/{id}/orderbook` |
| `iter_contracts` / `iter_questions` | offset paging | cursor paging |

Query parameters pass straight through, so anything the native API accepts works here. `None` values are dropped before the request is sent.

**Paging caps matter.** Gamma returns at most 100 records per request and silently ignores a larger `limit`, and Kalshi returns a cursor you must follow. Use the `iter_*` helpers when you want everything:

```python
async with PolymarketRest() as polymarket:
    async for contract in polymarket.iter_contracts(closed=False, order="volume24hr"):
        ...
```

## Speed

Batch requests are where the time goes, not parsing — decoding is roughly 15 µs per contract. Fetch concurrently:

```python
async with PolymarketRest() as polymarket:
    responses = await polymarket.fetch_many(ids, concurrency=8)  # ~3.8x faster than a loop
```

Rate limits and transient 5xx responses are retried with exponential backoff and jitter. A client takes `retries`, `backoff`, and `timeout` if you want to tune that:

```python
PolymarketRest(retries=4, timeout=10.0)
```

## Order books

Both exchanges are normalized to a single direction so books are comparable: `bids` are what buyers of `Yes` will pay, `asks` what sellers of `Yes` will take. Kalshi publishes resting bids per side, and a bid of `p` on `No` is an offer of `1 - p` on `Yes`, so `predmarket` complements it into the ask side. `best_bid`, `best_ask`, and `spread` come for free.

## Websocket

```python
import asyncio

from predmarket import PolymarketWS


async def main() -> None:
    async with PolymarketWS.connect() as socket:
        stream = PolymarketWS(socket).stream(["<asset_id>"])
        async for update in stream:
            print(type(update).__name__, update.model_dump_json())


asyncio.run(main())
```

`stream` yields typed models — `BookSnapshot`, `BookDelta`, `Trade`, or `Ticker` — so your editor autocompletes every field. See [`examples/stream_polymarket.py`](examples/stream_polymarket.py) for a runnable version that streams the busiest live markets.

The market channel rejects application-level `PING` frames (they come back as `INVALID OPERATION`), so `connect()` sends nothing extra and relies on protocol-level pings. Kalshi's parser is implemented but its socket client is not yet — Kalshi requires authenticated websockets.

## Errors

Failures raise subclasses of `PredmarketError`, importable from `predmarket` or `predmarket.errors`: `APIError` when an exchange answers with a non-success status (it carries `status_code` and `body`), and `TransportError` when the request never produced a response.

## Not covered yet

Trading, authenticated endpoints, and Kalshi websockets. Everything here reads public market data.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run pyright
uv run python examples/stream_polymarket.py
```

## More Information

`predmarket` is under rapid development. Expect breaking changes unless indicated otherwise.
