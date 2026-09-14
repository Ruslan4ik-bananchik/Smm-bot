from __future__ import annotations

from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort


class ActivateTechnicalTask:
    def __init__(self, repo: TechnicalTaskRepositoryPort):
        self.repo = repo

    async def execute(self, applicant_chat_id: int) -> None:
        await self.repo.mark_technical_task_started(applicant_chat_id)
