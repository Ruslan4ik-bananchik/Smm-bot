from __future__ import annotations

from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort


class CreateApplicationReview:
    def __init__(self, repo: ApplicationReviewRepositoryPort):
        self.repo = repo

    async def execute(
        self,
        token: str,
        manager_user_id: int,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        application_text: str,
        video_format: str | None,
        video_format_code: str | None,
        business_connection_id: str | None,
    ) -> None:
        await self.repo.create_application_review(
            token=token,
            manager_user_id=manager_user_id,
            applicant_user_id=applicant_user_id,
            applicant_chat_id=applicant_chat_id,
            applicant_username=applicant_username,
            application_text=application_text,
            video_format=video_format,
            video_format_code=video_format_code,
            business_connection_id=business_connection_id,
        )
