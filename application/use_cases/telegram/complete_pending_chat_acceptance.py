from __future__ import annotations

from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort


class CompletePendingChatAcceptance:
    def __init__(self, repo: TechnicalTaskRepositoryPort):
        self.repo = repo

    async def execute(self, *, applicant_user_id: int, target_chat_id: int) -> bool:
        return await self.repo.remove_pending_chat_acceptance(applicant_user_id, target_chat_id)
