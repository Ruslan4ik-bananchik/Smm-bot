from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationReviewResolutionDTO:
    applicant_chat_id: int
    applicant_user_id: int
    business_connection_id: str | None
    video_format: str | None
    video_format_code: str | None
    status: str
    was_updated: bool
