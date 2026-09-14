from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskReviewCallbackResultDTO:
    applicant_chat_id: int
    applicant_user_id: int
    business_connection_id: str
    status: str
