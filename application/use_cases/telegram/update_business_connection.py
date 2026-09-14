from __future__ import annotations

from application.ports.outbound.conversation_repository import ConversationRepositoryPort


class UpdateBusinessConnection:
    def __init__(self, repo: ConversationRepositoryPort):
        self.repo = repo

    async def execute(self, connection_id: str, owner_user_id: int, is_enabled: bool) -> None:
        await self.repo.upsert_business_connection(connection_id=connection_id, owner_user_id=owner_user_id, is_enabled=is_enabled)
