from __future__ import annotations

from application.dtos.technical_task_review_callback_result import TechnicalTaskReviewCallbackResultDTO
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.exceptions.errors import (
    ManagerNotConfiguredError,
    ReviewAccessDeniedError,
    ReviewAlreadyProcessedError,
    ReviewBusinessConnectionMissingError,
    ReviewNotFoundError,
    ReviewPayloadInvalidError,
)


class HandleTechnicalTaskReviewCallback:
    CALLBACK_PREFIX = "tech_review"

    def __init__(self, repo: TechnicalTaskRepositoryPort, manager_user_id: int | None):
        self.repo = repo
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, payload: str | None) -> TechnicalTaskReviewCallbackResultDTO:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise ReviewAccessDeniedError()

        raw_payload = payload or ""
        parts = raw_payload.split(":", 2)
        if len(parts) != 3 or parts[0] != self.CALLBACK_PREFIX:
            raise ReviewPayloadInvalidError()

        _, action, token = parts
        if action not in {"approve", "reject"}:
            raise ReviewPayloadInvalidError()

        resolution = await self.repo.resolve_technical_task_review(token=token, approved=(action == "approve"))
        if resolution is None:
            raise ReviewNotFoundError()
        if not resolution.was_updated:
            raise ReviewAlreadyProcessedError()
        if not resolution.business_connection_id:
            raise ReviewBusinessConnectionMissingError()

        return TechnicalTaskReviewCallbackResultDTO(
            applicant_chat_id=resolution.applicant_chat_id,
            applicant_user_id=resolution.applicant_user_id,
            business_connection_id=resolution.business_connection_id,
            status=resolution.status,
        )
