from __future__ import annotations

from application.dtos.troll_report_dispatch import TrollReportDispatchDTO
from application.dtos.troll_report_view_data import TrollReportViewDataDTO


class PrepareTrollReportDispatch:
    def __init__(self, review_chat_id: int, troll_report_thread_id: int | None):
        self.review_chat_id = review_chat_id
        self.troll_report_thread_id = troll_report_thread_id

    def execute(
        self,
        *,
        applicant_user_id: int,
        applicant_username: str | None,
        source_message_link: str | None,
        troll_text: str,
    ) -> TrollReportDispatchDTO:
        return TrollReportDispatchDTO(
            review_chat_id=self.review_chat_id,
            message_thread_id=self.troll_report_thread_id,
            view_data=TrollReportViewDataDTO(
                applicant_user_id=applicant_user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                troll_text=troll_text,
            ),
        )
