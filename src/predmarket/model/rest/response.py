from typing import Any

from pydantic import BaseModel, Field

__all__ = ["Response"]


class Response[T](BaseModel):
    """Generic API response wrapper.

    For list payloads it also supports ``len(response)`` and ``response[0]``;
    iterate with ``response.data``. Iteration over the model itself stays
    pydantic's field iteration so ``dict(response)`` keeps working.
    """

    data: T
    metadata: dict[str, Any] = Field(default_factory=dict)

    def merge(self, other: "Response[list[Any]]") -> "Response[list[Any]]":
        """Merge two list-based responses."""
        if not isinstance(self.data, list) or not isinstance(other.data, list):
            raise TypeError("Both responses must have list data to merge.")
        return Response(
            data=self.data + other.data,
            metadata={**self.metadata, **other.metadata},
        )

    def __len__(self) -> int:
        if isinstance(self.data, list):
            return len(self.data)
        raise TypeError(f"{type(self).__name__} wrapping {type(self.data).__name__} has no length")

    def __getitem__(self, index: int) -> Any:
        if isinstance(self.data, list):
            return self.data[index]
        raise TypeError(
            f"{type(self).__name__} wrapping {type(self.data).__name__} is not indexable"
        )

    def __repr__(self) -> str:
        inner = f"{len(self.data)} items" if isinstance(self.data, list) else repr(self.data)
        return f"Response({inner})"
