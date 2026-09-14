from __future__ import annotations

from application.ports.outbound.conversation_repository import ConversationRepositoryPort


class CloseDialog:
    def __init__(self, repo: ConversationRepositoryPort):
        self.repo = repo

    async def execute(self, dialog_id: int) -> None:
        await self.repo.close_dialog(dialog_id)
