from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskKeyLogNotificationDTO:
    log_id: int
    applicant_chat_id: int
    applicant_user_id: int | None
    applicant_username: str | None
    event_type: str
    event_data: str | None
    created_at: str
