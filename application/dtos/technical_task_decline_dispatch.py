from __future__ import annotations

from dataclasses import dataclass

from application.dtos.technical_task_decline_view_data import TechnicalTaskDeclineViewDataDTO


@dataclass(frozen=True)
class TechnicalTaskDeclineDispatchDTO:
    review_chat_id: int
    message_thread_id: int | None
    view_data: TechnicalTaskDeclineViewDataDTO
