from __future__ import annotations

from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.exceptions.errors import ManagerNotConfiguredError, ProductKeyUploadAccessDeniedError
from domain.services.product_key_parser import ProductKeyParser


class UploadProductKeys:
    def __init__(self, repo: TechnicalTaskRepositoryPort, manager_user_id: int | None):
        self.repo = repo
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, raw_text: str) -> int:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise ProductKeyUploadAccessDeniedError()

        keys = ProductKeyParser.parse(raw_text)
        return await self.repo.add_product_keys(keys)
