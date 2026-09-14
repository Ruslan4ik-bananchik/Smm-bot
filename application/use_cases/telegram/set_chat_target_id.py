from __future__ import annotations

from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from domain.exceptions.errors import ChatTargetIdInvalidError, ManagerNotConfiguredError, NotManagerError


class SetChatTargetId:
    ASSET_NAME = "chat_target_id"

    def __init__(self, repo: TelegramAssetRepositoryPort, manager_user_id: int | None):
        self.repo = repo
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, value: str) -> None:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise NotManagerError()
        try:
            chat_id = int(value.strip())
        except ValueError as exc:
            raise ChatTargetIdInvalidError() from exc
        await self.repo.save_asset_text(self.ASSET_NAME, str(chat_id), self.manager_user_id)
