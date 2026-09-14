from __future__ import annotations

from abc import ABC, abstractmethod

from application.dtos.application_review_dispatch import ApplicationReviewDispatchDTO
from application.dtos.processed_incoming_message import ProcessedIncomingMessageDTO
from application.dtos.technical_task_decline_dispatch import TechnicalTaskDeclineDispatchDTO
from application.dtos.technical_task_review_dispatch import TechnicalTaskReviewDispatchDTO
from application.dtos.troll_report_dispatch import TrollReportDispatchDTO


class IncomingMessageResultPublisherPort(ABC):
    @abstractmethod
    async def publish_reply(
        self,
        result: ProcessedIncomingMessageDTO,
        *,
        chat_id: int,
        business_connection_id: str | None,
    ) -> None: ...

    @abstractmethod
    async def publish_application_review(self, dispatch: ApplicationReviewDispatchDTO | None) -> None: ...

    @abstractmethod
    async def publish_technical_task_review(self, dispatch: TechnicalTaskReviewDispatchDTO | None) -> bool: ...

    @abstractmethod
    async def publish_technical_task_decline(self, dispatch: TechnicalTaskDeclineDispatchDTO | None) -> None: ...

    @abstractmethod
    async def publish_troll_report(self, dispatch: TrollReportDispatchDTO | None) -> None: ...
