from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskReviewViewDataDTO:
    applicant_user_id: int
    applicant_username: str | None
    source_message_link: str | None
    submission_text: str
