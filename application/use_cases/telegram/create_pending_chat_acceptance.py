from __future__ import annotations

from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort


class CreatePendingChatAcceptance:
    def __init__(self, repo: TechnicalTaskRepositoryPort):
        self.repo = repo

    async def execute(self, *, applicant_chat_id: int, applicant_user_id: int, target_chat_id: int) -> None:
        await self.repo.add_pending_chat_acceptance(
            applicant_chat_id=applicant_chat_id,
            applicant_user_id=applicant_user_id,
            target_chat_id=target_chat_id,
        )
