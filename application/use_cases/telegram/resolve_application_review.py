from __future__ import annotations

from application.dtos.application_review_resolution import ApplicationReviewResolutionDTO
from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort


class ResolveApplicationReview:
    def __init__(self, repo: ApplicationReviewRepositoryPort):
        self.repo = repo

    async def execute(self, token: str, approved: bool) -> ApplicationReviewResolutionDTO | None:
        return await self.repo.resolve_application_review(token=token, approved=approved)
