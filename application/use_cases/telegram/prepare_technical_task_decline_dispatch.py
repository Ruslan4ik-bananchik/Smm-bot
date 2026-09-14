from __future__ import annotations

from application.dtos.technical_task_decline_dispatch import TechnicalTaskDeclineDispatchDTO
from application.dtos.technical_task_decline_view_data import TechnicalTaskDeclineViewDataDTO


class PrepareTechnicalTaskDeclineDispatch:
    def __init__(self, review_chat_id: int, technical_task_decline_thread_id: int | None):
        self.review_chat_id = review_chat_id
        self.technical_task_decline_thread_id = technical_task_decline_thread_id

    def execute(
        self,
        *,
        applicant_user_id: int,
        applicant_username: str | None,
        source_message_link: str | None,
        decline_text: str,
        product_key: str | None,
        key_count: int,
    ) -> TechnicalTaskDeclineDispatchDTO:
        return TechnicalTaskDeclineDispatchDTO(
            review_chat_id=self.review_chat_id,
            message_thread_id=self.technical_task_decline_thread_id,
            view_data=TechnicalTaskDeclineViewDataDTO(
                applicant_user_id=applicant_user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                decline_text=decline_text,
                product_key=product_key,
                key_count=key_count,
            ),
        )
