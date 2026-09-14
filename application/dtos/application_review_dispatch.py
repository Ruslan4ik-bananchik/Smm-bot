from __future__ import annotations

from dataclasses import dataclass

from application.dtos.application_review_view_data import ApplicationReviewViewDataDTO


@dataclass(frozen=True)
class ApplicationReviewDispatchDTO:
    review_chat_id: int
    message_thread_id: int | None
    view_data: ApplicationReviewViewDataDTO
    approve_callback_data: str
    reject_callback_data: str
