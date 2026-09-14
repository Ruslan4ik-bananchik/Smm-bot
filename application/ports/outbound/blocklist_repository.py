from __future__ import annotations

from abc import ABC, abstractmethod


class BlocklistRepositoryPort(ABC):
    @abstractmethod
    async def add_user(self, user_id: int, reason: str | None = None) -> None: ...

    @abstractmethod
    async def remove_user(self, user_id: int) -> bool: ...

    @abstractmethod
    async def contains_user(self, user_id: int) -> bool: ...
