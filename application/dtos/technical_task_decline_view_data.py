from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskDeclineViewDataDTO:
    applicant_user_id: int
    applicant_username: str | None
    source_message_link: str | None
    decline_text: str
    product_key: str | None = None
    key_count: int = 0
