from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import ClassVar

from websockets.asyncio.client import ClientConnection

from .normalize import UnifiedModel

__all__ = ["BaseWebSocket"]


class BaseWebSocket(ABC):
    """Shared contract for exchange websocket clients."""

    URL: ClassVar[str]

    def __init__(self, websocket: ClientConnection) -> None:
        self.socket = websocket

    @abstractmethod
    def stream(self, ids: list[str]) -> AsyncIterator[UnifiedModel]:
        """Yield normalized messages for the given market ids."""
