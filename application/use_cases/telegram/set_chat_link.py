from __future__ import annotations

from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from domain.exceptions.errors import ManagerNotConfiguredError, NotManagerError


class SetChatLink:
    ASSET_NAME = "chat_link"

    def __init__(self, repo: TelegramAssetRepositoryPort, manager_user_id: int | None):
        self.repo = repo
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, value: str) -> None:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise NotManagerError()
        await self.repo.save_asset_text(self.ASSET_NAME, value.strip(), self.manager_user_id)
