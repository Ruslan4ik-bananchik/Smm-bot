from __future__ import annotations

from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort


class GetChatTargetId:
    ASSET_NAME = "chat_target_id"

    def __init__(self, repo: TelegramAssetRepositoryPort):
        self.repo = repo

    async def execute(self) -> int | None:
        raw_value = await self.repo.get_asset_text(self.ASSET_NAME)
        if raw_value is None:
            return None
        try:
            return int(raw_value.strip())
        except ValueError:
            return None
