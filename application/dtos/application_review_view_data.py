from __future__ import annotations

from dataclasses import dataclass

from application.dtos.application_form import ApplicationFormDTO


@dataclass(frozen=True)
class ApplicationReviewViewDataDTO:
    applicant_user_id: int
    applicant_username: str | None
    source_message_link: str | None
    application_form: ApplicationFormDTO
