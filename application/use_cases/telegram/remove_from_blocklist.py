from __future__ import annotations

from application.ports.outbound.blocklist_repository import BlocklistRepositoryPort


class RemoveFromBlocklist:
    def __init__(self, repo: BlocklistRepositoryPort):
        self.repo = repo

    async def execute(self, user_id: int) -> bool:
        return await self.repo.remove_user(user_id)
