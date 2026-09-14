from __future__ import annotations

from application.ports.outbound.conversation_repository import ConversationRepositoryPort


class StoreDialogMessage:
    def __init__(self, repo: ConversationRepositoryPort):
        self.repo = repo

    async def execute(
        self,
        dialog_id: int,
        text: str,
        auto_close_eligible: bool = False,
        force_auto_close: bool = False,
    ) -> None:
        await self.repo.append_message(
            dialog_id,
            text,
            auto_close_eligible=auto_close_eligible,
            force_auto_close=force_auto_close,
        )
