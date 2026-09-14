from __future__ import annotations

from dataclasses import dataclass

from application.dtos.troll_report_view_data import TrollReportViewDataDTO


@dataclass(frozen=True)
class TrollReportDispatchDTO:
    review_chat_id: int
    message_thread_id: int | None
    view_data: TrollReportViewDataDTO
