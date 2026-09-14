from __future__ import annotations

from application.ports.outbound.blocklist_repository import BlocklistRepositoryPort


class AddToBlocklist:
    def __init__(self, repo: BlocklistRepositoryPort):
        self.repo = repo

    async def execute(self, user_id: int, reason: str | None = None) -> None:
        await self.repo.add_user(user_id, reason)
