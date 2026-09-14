from __future__ import annotations

from abc import ABC, abstractmethod

from application.dtos.application_review_resolution import ApplicationReviewResolutionDTO


class ApplicationReviewRepositoryPort(ABC):
    @abstractmethod
    async def create_application_review(
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
    ) -> None: ...

    @abstractmethod
    async def resolve_application_review(self, token: str, approved: bool) -> ApplicationReviewResolutionDTO | None: ...
