from __future__ import annotations

import secrets

from application.dtos.anwser import AnwserDTO
from application.dtos.application_review_dispatch import ApplicationReviewDispatchDTO
from application.dtos.application_review_view_data import ApplicationReviewViewDataDTO
from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort
from domain.exceptions.errors import ManagerNotConfiguredError, UnhandledException


class PrepareApplicationReviewDispatch:
    CALLBACK_PREFIX = "review"

    def __init__(
        self,
        repo: ApplicationReviewRepositoryPort,
        manager_user_id: int | None,
        review_chat_id: int,
        application_review_thread_id: int | None,
    ):
        self.repo = repo
        self.manager_user_id = manager_user_id
        self.review_chat_id = review_chat_id
        self.application_review_thread_id = application_review_thread_id

    async def execute(
        self,
        *,
        result: AnwserDTO,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        source_message_link: str | None,
        business_connection_id: str | None,
    ) -> ApplicationReviewDispatchDTO:
        form = result.application_form
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if form is None:
            raise UnhandledException()

        token = secrets.token_urlsafe(9)
        await self.repo.create_application_review(
            token=token,
            manager_user_id=self.manager_user_id,
            applicant_user_id=applicant_user_id,
            applicant_chat_id=applicant_chat_id,
            applicant_username=applicant_username,
            application_text="",
            video_format=form.video_format,
            video_format_code=form.video_format_code,
            business_connection_id=business_connection_id,
        )

        return ApplicationReviewDispatchDTO(
            review_chat_id=self.review_chat_id,
            message_thread_id=self.application_review_thread_id,
            view_data=ApplicationReviewViewDataDTO(
                applicant_user_id=applicant_user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                application_form=form,
            ),
            approve_callback_data=f"{self.CALLBACK_PREFIX}:approve:{token}",
            reject_callback_data=f"{self.CALLBACK_PREFIX}:reject:{token}",
        )
