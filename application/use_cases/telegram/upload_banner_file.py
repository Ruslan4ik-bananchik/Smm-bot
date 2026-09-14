from __future__ import annotations

from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from domain.exceptions.errors import BannerUploadAccessDeniedError, ManagerNotConfiguredError


class UploadBannerFile:
    ASSET_NAME = "shorts_banner"

    def __init__(self, repo: TelegramAssetRepositoryPort, manager_user_id: int | None):
        self.repo = repo
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, file_id: str, file_name: str | None) -> None:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise BannerUploadAccessDeniedError()
        await self.repo.save_asset_file(self.ASSET_NAME, file_id, file_name, self.manager_user_id)
