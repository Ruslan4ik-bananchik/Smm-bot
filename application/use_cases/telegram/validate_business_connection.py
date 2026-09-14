from __future__ import annotations

from application.ports.outbound.conversation_repository import ConversationRepositoryPort


class ValidateBusinessConnection:
    def __init__(self, manager_user_id: int, repo: ConversationRepositoryPort):
        self.manager_user_id = manager_user_id
        self.repo = repo

    async def execute(self, connection_id: str) -> bool:
        owner_user_id = await self.repo.get_business_connection_owner(connection_id)
        return owner_user_id == self.manager_user_id
