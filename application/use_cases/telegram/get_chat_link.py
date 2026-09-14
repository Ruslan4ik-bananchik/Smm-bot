from __future__ import annotations

from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort


class GetChatLink:
    ASSET_NAME = "chat_link"

    def __init__(self, repo: TelegramAssetRepositoryPort):
        self.repo = repo

    async def execute(self) -> str | None:
        return await self.repo.get_asset_text(self.ASSET_NAME)
