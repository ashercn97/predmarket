from predmarket.model.rest import Contract, Price

KALSHI_MARKET = {
    "ticker": "KXELONMARS-99",
    "title": "Will Elon Musk visit Mars before Aug 1, 2099?",
    "last_price_dollars": "0.1000",
    "yes_bid_dollars": "0.1000",
    "yes_ask_dollars": "0.1300",
    "volume_fp": "127815.74",
}

POLYMARKET_MARKET = {
    "id": "559651",
    "question": "Xi Jinping out before 2027?",
    "outcomes": '["Yes", "No"]',
    "lastTradePrice": 0.015,
    "bestBid": 0.017,
    "bestAsk": 0.018,
    "volume": "17392796.37",
    "liquidity": "295974.65",
}


def test_kalshi_price_reads_dollar_and_fixed_fields():
    price = Price.from_kalshi(KALSHI_MARKET)
    assert price.bid == 0.10
    assert price.ask == 0.13
    assert price.price == 0.10
    assert price.volume == 127815.74


def test_kalshi_price_falls_back_to_legacy_cents():
    price = Price.from_kalshi({"last_price": 25, "yes_bid": 20, "yes_ask": 30, "volume": 10})
    assert price.price == 0.25
    assert price.bid == 0.20
    assert price.ask == 0.30
    assert price.volume == 10.0


def test_kalshi_price_handles_missing_fields():
    assert Price.from_kalshi({}) == Price()


def test_polymarket_price_reads_gamma_fields():
    price = Price.from_polymarket(POLYMARKET_MARKET)
    assert price.price == 0.015
    assert price.bid == 0.017
    assert price.ask == 0.018


def test_polymarket_outcomes_decode_json_string():
    contract = Contract.from_polymarket(POLYMARKET_MARKET)
    assert contract.outcomes == ["Yes", "No"]
    assert contract.platform == "polymarket"
    assert contract.price == 0.015


def test_kalshi_contract_normalizes_binary_outcomes():
    contract = Contract.from_kalshi(KALSHI_MARKET)
    assert contract.outcomes == ["Yes", "No"]
    assert contract.id == "KXELONMARS-99"
    assert contract.raw == KALSHI_MARKET
