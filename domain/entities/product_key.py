from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductKey:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Product key cannot be empty")

    def __str__(self) -> str:
        return self.value
