from __future__ import annotations

import secrets

from application.dtos.technical_task_review_dispatch import TechnicalTaskReviewDispatchDTO
from application.dtos.technical_task_review_view_data import TechnicalTaskReviewViewDataDTO
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.exceptions.errors import ManagerNotConfiguredError


class PrepareTechnicalTaskReviewDispatch:
    CALLBACK_PREFIX = "tech_review"

    def __init__(
        self,
        repo: TechnicalTaskRepositoryPort,
        manager_user_id: int | None,
        review_chat_id: int,
        technical_task_review_thread_id: int | None,
    ):
        self.repo = repo
        self.manager_user_id = manager_user_id
        self.review_chat_id = review_chat_id
        self.technical_task_review_thread_id = technical_task_review_thread_id

    async def execute(
        self,
        *,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        source_message_link: str | None,
        submission_text: str,
        business_connection_id: str | None,
    ) -> TechnicalTaskReviewDispatchDTO:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()

        token = secrets.token_urlsafe(9)
        await self.repo.create_technical_task_review(
            token=token,
            manager_user_id=self.manager_user_id,
            applicant_user_id=applicant_user_id,
            applicant_chat_id=applicant_chat_id,
            applicant_username=applicant_username,
            submission_text=submission_text,
            business_connection_id=business_connection_id,
        )
        await self.repo.mark_technical_task_submitted(
            applicant_chat_id=applicant_chat_id,
            submission_text=submission_text,
        )
        return TechnicalTaskReviewDispatchDTO(
            review_chat_id=self.review_chat_id,
            message_thread_id=self.technical_task_review_thread_id,
            view_data=TechnicalTaskReviewViewDataDTO(
                applicant_user_id=applicant_user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                submission_text=submission_text,
            ),
            approve_callback_data=f"{self.CALLBACK_PREFIX}:approve:{token}",
            reject_callback_data=f"{self.CALLBACK_PREFIX}:reject:{token}",
        )
