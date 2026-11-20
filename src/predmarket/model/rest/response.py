from typing import Any

from pydantic import BaseModel, Field


class Response[T](BaseModel):
    """Generic API response wrapper."""

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
