from __future__ import annotations

from dataclasses import dataclass

from application.dtos.application_review_dispatch import ApplicationReviewDispatchDTO
from application.dtos.technical_task_decline_dispatch import TechnicalTaskDeclineDispatchDTO
from application.dtos.technical_task_key_view import TechnicalTaskKeyViewDTO
from application.dtos.technical_task_review_dispatch import TechnicalTaskReviewDispatchDTO
from application.dtos.troll_report_dispatch import TrollReportDispatchDTO


@dataclass(frozen=True)
class ProcessedIncomingMessageDTO:
    reply_text: str
    review_dispatch: ApplicationReviewDispatchDTO | None = None
    technical_task_review_dispatch: TechnicalTaskReviewDispatchDTO | None = None
    technical_task_decline_dispatch: TechnicalTaskDeclineDispatchDTO | None = None
    troll_report_dispatch: TrollReportDispatchDTO | None = None
    technical_task_key: TechnicalTaskKeyViewDTO | None = None
