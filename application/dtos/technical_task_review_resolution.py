from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskReviewResolutionDTO:
    applicant_chat_id: int
    applicant_user_id: int
    business_connection_id: str | None
    status: str
    was_updated: bool
