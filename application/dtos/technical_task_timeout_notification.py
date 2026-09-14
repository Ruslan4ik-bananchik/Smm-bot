from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskTimeoutNotificationDTO:
    applicant_chat_id: int
    task_type: str
    timed_out_at: str
    business_connection_id: str | None
    applicant_user_id: int | None = None
    applicant_username: str | None = None
    product_key: str | None = None
    key_count: int = 0
    notified_at: str | None = None
