import json

import httpx
import pytest

from predmarket import KalshiRest, PolymarketRest
from predmarket.errors import APIError
from predmarket.model.rest import Contract, Response


def market(mid: str) -> dict:
    return {
        "id": mid,
        "question": f"Question {mid}?",
        "outcomes": '["Yes", "No"]',
        "lastTradePrice": 0.5,
    }


def kalshi_market(ticker: str) -> dict:
    return {"ticker": ticker, "title": f"Kalshi {ticker}", "last_price_dollars": "0.5"}


def client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_client_is_a_context_manager_and_closes():
    async with PolymarketRest() as polymarket:
        assert polymarket._owns_client is True


async def test_iter_contracts_pages_polymarket_with_offset():
    seen_offsets = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params.get("offset", 0))
        seen_offsets.append(offset)
        count = 3 if offset < 6 else 1
        return httpx.Response(200, json=[market(f"{offset}-{i}") for i in range(count)])

    async with PolymarketRest(client_for(handler)) as polymarket:
        contracts = [c async for c in polymarket.iter_contracts(page_size=3, closed=False)]

    assert seen_offsets == [0, 3, 6]
    assert len(contracts) == 7
    assert all(isinstance(c, Contract) for c in contracts)


async def test_iter_contracts_stops_on_empty_page():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    async with PolymarketRest(client_for(handler)) as polymarket:
        assert [c async for c in polymarket.iter_contracts()] == []


async def test_iter_contracts_follows_kalshi_cursor():
    seen_cursors = []

    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        seen_cursors.append(cursor)
        if cursor is None:
            return httpx.Response(
                200, json={"markets": [kalshi_market("A"), kalshi_market("B")], "cursor": "next"}
            )
        return httpx.Response(200, json={"markets": [kalshi_market("C")], "cursor": ""})

    async with KalshiRest(client_for(handler)) as kalshi:
        contracts = [c async for c in kalshi.iter_contracts(page_size=2)]

    assert seen_cursors == [None, "next"]
    assert [c.id for c in contracts] == ["A", "B", "C"]


async def test_retries_transient_status_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, json=market("1"))

    async with PolymarketRest(client_for(handler), retries=1, backoff=0.0) as polymarket:
        result = await polymarket.fetch_contract("1")

    assert calls["n"] == 2
    assert result.data.id == "1"


async def test_does_not_retry_client_errors():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, json={"error": "not found"})

    async with PolymarketRest(client_for(handler), retries=2) as polymarket:
        with pytest.raises(APIError) as exc:
            await polymarket.fetch_contract("missing")

    assert calls["n"] == 1
    assert exc.value.status_code == 404


async def test_response_behaves_like_its_list():
    response = Response[list[dict]](data=[market("1"), market("2")])
    assert len(response) == 2
    assert response[1]["id"] == "2"
    assert repr(response) == "Response(2 items)"
    assert [row["id"] for row in response.data] == ["1", "2"]
    # pydantic field iteration is preserved
    assert dict(response).keys() == {"data", "metadata"}


async def test_response_rejects_sequence_use_for_scalars():
    response = Response[dict](data=market("1"))
    with pytest.raises(TypeError):
        len(response)


async def test_kalshi_price_reads_dollars_off_the_wire():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "market": {
                    "ticker": "T",
                    "last_price_dollars": "0.4200",
                    "yes_bid_dollars": "0.4000",
                    "yes_ask_dollars": "0.4400",
                    "volume_fp": "1234.50",
                }
            },
        )

    async with KalshiRest(client_for(handler)) as kalshi:
        price = (await kalshi.fetch_price("T")).data

    assert (price.bid, price.ask, price.price, price.volume) == (0.4, 0.44, 0.42, 1234.5)


async def test_polymarket_orderbook_resolves_primary_token():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if "gamma-api" in str(request.url):
            return httpx.Response(
                200,
                json={"id": "9", "clobTokenIds": json.dumps(["tok-yes", "tok-no"])},
            )
        return httpx.Response(
            200,
            json={
                "bids": [{"price": "0.40", "size": "100"}],
                "asks": [{"price": "0.44", "size": "50"}],
            },
        )

    async with PolymarketRest(client_for(handler)) as polymarket:
        book = await polymarket.fetch_orderbook("9")

    assert book.metadata["token_id"] == "tok-yes"
    assert "token_id=tok-yes" in seen[1]
    assert book.data.best_bid == 0.40
    assert book.data.best_ask == 0.44
