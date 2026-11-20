"""Stream order book updates for the busiest live Polymarket markets."""

import asyncio
import json

from predmarket import PolymarketRest, PolymarketWS


async def main() -> None:
    async with PolymarketRest() as polymarket:
        contracts = await polymarket.fetch_contracts(
            limit=5,
            closed=False,
            order="volume24hr",
            ascending=False,
        )

    assets = [json.loads(contract.raw["clobTokenIds"])[0] for contract in contracts.data]
    for contract in contracts.data:
        print(f"{contract.id}  {contract.price}  {contract.question}")

    async with PolymarketWS.connect() as socket:
        async for update in PolymarketWS(socket).stream(assets):
            print(update.model_dump_json(exclude_none=True))


if __name__ == "__main__":
    asyncio.run(main())
