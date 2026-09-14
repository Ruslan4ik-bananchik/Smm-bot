from __future__ import annotations

from dataclasses import dataclass

from application.dtos.technical_task_review_view_data import TechnicalTaskReviewViewDataDTO


@dataclass(frozen=True)
class TechnicalTaskReviewDispatchDTO:
    review_chat_id: int
    message_thread_id: int | None
    view_data: TechnicalTaskReviewViewDataDTO
    approve_callback_data: str
    reject_callback_data: str
