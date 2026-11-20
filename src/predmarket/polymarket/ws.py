import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, ClassVar

from websockets.asyncio.client import ClientConnection, connect

from predmarket.model.ws import BaseWebSocket, UnifiedModel, normalize_message

__all__ = ["PolymarketWS"]


def _rows(message: str | bytes) -> list[dict[str, Any]]:
    """Decode one websocket frame into row dicts.

    Polymarket batches updates into a JSON array and also sends single objects,
    plus plain-text frames such as ``INVALID OPERATION`` that carry no payload.
    """
    try:
        payload = json.loads(message)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    match payload:
        case dict():
            return [payload]
        case list():
            return [row for row in payload if isinstance(row, dict)]
        case _:
            return []


class PolymarketWS(BaseWebSocket):
    """Stream Polymarket CLOB order book and trade updates."""

    URL: ClassVar[str] = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def __init__(self, websocket: ClientConnection) -> None:
        super().__init__(websocket)

    async def stream(self, ids: list[str]) -> AsyncIterator[UnifiedModel]:
        """Subscribe to the given asset ids and yield normalized updates."""
        await self.socket.send(json.dumps({"assets_ids": ids, "type": "market"}))
        async for message in self.socket:
            for row in _rows(message):
                if unified := normalize_message(row, source="polymarket"):
                    yield unified

    @classmethod
    @asynccontextmanager
    async def connect(cls) -> AsyncIterator[ClientConnection]:
        """Open a market-channel socket.

        The market channel does not accept application-level ``PING`` frames
        (they come back as ``INVALID OPERATION``), so liveness rides on the
        protocol-level pings that ``websockets`` sends on its own.
        """
        async with connect(cls.URL) as socket:
            yield socket
