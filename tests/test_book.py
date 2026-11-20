from predmarket.model.rest import OrderBook, Side

KALSHI_PAYLOAD = {
    "orderbook_fp": {
        "yes_dollars": [["0.0100", "3020.78"], ["0.1000", "379.78"]],
        "no_dollars": [["0.1000", "20.00"], ["0.8700", "1562.36"]],
    }
}

POLYMARKET_PAYLOAD = {
    "market": "0xa467",
    "timestamp": "1782753357257",
    "bids": [{"price": "0.08", "size": "10"}, {"price": "0.10", "size": "5"}],
    "asks": [{"price": "0.13", "size": "7"}, {"price": "0.11", "size": "3"}],
}


def test_kalshi_book_orders_bids_desc_and_asks_asc():
    book = OrderBook.from_kalshi("KXELONMARS-99", KALSHI_PAYLOAD)
    assert book.platform == "kalshi"
    assert [level.price for level in book.bids] == [0.10, 0.01]
    # No bids at 0.87 and 0.10 become Yes asks at 0.13 and 0.90.
    assert [level.price for level in book.asks] == [0.13, 0.90]
    assert all(level.side is Side.YES for level in book.bids + book.asks)


def test_kalshi_book_top_of_book():
    book = OrderBook.from_kalshi("KXELONMARS-99", KALSHI_PAYLOAD)
    assert book.best_bid == 0.10
    assert book.best_ask == 0.13
    assert book.spread == 0.03


def test_kalshi_book_handles_empty_depth():
    book = OrderBook.from_kalshi("KXELONMARS-99", {"orderbook_fp": {}})
    assert book.bids == []
    assert book.asks == []
    assert book.best_bid is None
    assert book.spread is None


def test_kalshi_book_reads_legacy_cents_payload():
    book = OrderBook.from_kalshi("T", {"orderbook": {"yes": [[10, 5]], "no": [[87, 3]]}})
    assert book.best_bid == 0.10
    assert book.best_ask == 0.13


def test_polymarket_book_sorts_both_sides():
    book = OrderBook.from_polymarket("559651", POLYMARKET_PAYLOAD)
    assert [level.price for level in book.bids] == [0.10, 0.08]
    assert [level.price for level in book.asks] == [0.11, 0.13]
    assert book.best_bid == 0.10
    assert book.best_ask == 0.11
    assert book.timestamp is not None


def test_polymarket_book_skips_malformed_levels():
    book = OrderBook.from_polymarket("id", {"bids": [{"price": "0.05"}, "junk"]})
    assert book.bids == []
