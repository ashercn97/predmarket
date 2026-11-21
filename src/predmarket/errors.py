"""Errors raised by predmarket."""


class PredmarketError(Exception):
    """Base class for every error raised by predmarket."""


class APIError(PredmarketError):
    """An exchange responded with a non-success status."""

    def __init__(self, url: str, status_code: int, body: str) -> None:
        super().__init__(f"{url} returned {status_code}: {body}")
        self.url = url
        self.status_code = status_code
        self.body = body


class TransportError(PredmarketError):
    """The request failed before an exchange could respond."""
