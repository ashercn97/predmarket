from datetime import UTC, datetime

import pytest

from predmarket.model.ws import BookDelta, BookSnapshot, Exchange, Side, Trade, normalize_message

POLYMARKET_BOOK = {
    "event_type": "book",
    "market": "0xa467",
    "timestamp": "1782753357257",
    "bids": [{"price": "0.08", "size": "33343.4"}],
    "asks": [{"price": "0.09", "size": "163939.58"}],
}

POLYMARKET_TRADE = {
    "event_type": "last_trade_price",
    "market": "0xa467",
    "price": "0.09",
    "size": "219.2",
    "side": "SELL",
}

KALSHI_SNAPSHOT = {
    "type": "orderbook_snapshot",
    "msg": {
        "market_ticker": "KXELONMARS-99",
        "ts": "2026-11-20T19:48:52.413222Z",
        "yes_dollars": [["0.1000", "379.78"], ["0.0900", "1507.11"]],
        "no_dollars": [["0.8700", "1562.36"], ["0.8600", "91.40"]],
    },
}

KALSHI_SNAPSHOT_LEGACY = {
    "type": "orderbook_snapshot",
    "msg": {
        "market_ticker": "KXELONMARS-99",
        "yes": [[10, 500]],
        "no": [[87, 300]],
    },
}


def test_polymarket_book_normalizes_with_timestamp():
    parsed = normalize_message(POLYMARKET_BOOK, source="polymarket")
    assert isinstance(parsed, BookSnapshot)
    assert parsed.exchange is Exchange.POLYMARKET
    assert parsed.bids[0].price == 0.08
    assert parsed.bids[0].side is Side.BUY
    assert parsed.asks[0].side is Side.SELL
    assert parsed.timestamp == datetime.fromtimestamp(1782753357.257, tz=UTC)


def test_polymarket_trade_carries_side():
    parsed = normalize_message(POLYMARKET_TRADE, source=Exchange.POLYMARKET)
    assert isinstance(parsed, Trade)
    assert parsed.price == 0.09
    assert parsed.side is Side.SELL


def test_polymarket_unknown_event_is_skipped():
    assert normalize_message({"event_type": "tick_size_change"}, source="polymarket") is None


def test_kalshi_snapshot_complements_no_side_into_asks():
    parsed = normalize_message(KALSHI_SNAPSHOT, source="kalshi")
    assert isinstance(parsed, BookSnapshot)
    assert parsed.exchange is Exchange.KALSHI
    assert parsed.market_id == "KXELONMARS-99"
    assert [level.price for level in parsed.bids] == [0.10, 0.09]
    assert parsed.bids[0].size == 379.78
    assert parsed.bids[0].side is Side.YES
    # A No bid at 0.87 is a Yes ask at 0.13, with the same resting size.
    assert [level.price for level in parsed.asks] == [0.13, 0.14]
    assert parsed.asks[0].size == 1562.36
    assert parsed.timestamp == datetime(2026, 11, 20, 19, 48, 52, 413222, tzinfo=UTC)


def test_kalshi_snapshot_reads_legacy_cents():
    parsed = normalize_message(KALSHI_SNAPSHOT_LEGACY, source="kalshi")
    assert isinstance(parsed, BookSnapshot)
    assert [level.price for level in parsed.bids] == [0.10]
    assert [level.price for level in parsed.asks] == [0.13]


def test_kalshi_delta_orients_both_sides_to_yes():
    parsed = normalize_message(
        {
            "type": "orderbook_delta",
            "msg": {
                "market_ticker": "KXELONMARS-99",
                "yes_dollars": [["0.1100", "5"]],
                "no_dollars": [["0.8800", "7"]],
            },
        },
        source="kalshi",
    )
    assert isinstance(parsed, BookDelta)
    assert [(level.side, level.price) for level in parsed.deltas] == [
        (Side.YES, 0.11),
        (Side.YES, 0.12),
    ]


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="ftx"):
        normalize_message({}, source="ftx")
