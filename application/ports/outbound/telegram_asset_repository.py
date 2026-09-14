from __future__ import annotations

from abc import ABC, abstractmethod


class TelegramAssetRepositoryPort(ABC):
    @abstractmethod
    async def save_asset_file(self, name: str, file_id: str, file_name: str | None, owner: int) -> None: ...

    @abstractmethod
    async def get_asset_file(self, name: str) -> tuple[str, str | None] | None: ...

    @abstractmethod
    async def save_asset_text(self, name: str, value: str, owner: int) -> None: ...

    @abstractmethod
    async def get_asset_text(self, name: str) -> str | None: ...
