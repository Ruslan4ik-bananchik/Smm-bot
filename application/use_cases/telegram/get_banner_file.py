from __future__ import annotations

from application.dtos.telegram_asset_file_view import TelegramAssetFileViewDTO
from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from domain.exceptions.errors import BannerNotUploadedError


class GetBannerFile:
    ASSET_NAME = "shorts_banner"

    def __init__(self, repo: TelegramAssetRepositoryPort):
        self.repo = repo

    async def execute(self) -> TelegramAssetFileViewDTO:
        asset = await self.repo.get_asset_file(self.ASSET_NAME)
        if asset is None:
            raise BannerNotUploadedError()

        file_id, file_name = asset
        return TelegramAssetFileViewDTO(file_id=file_id, file_name=file_name)
