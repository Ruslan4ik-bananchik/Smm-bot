from __future__ import annotations

from abc import ABC, abstractmethod

from application.dtos.technical_task_key_log_notification import TechnicalTaskKeyLogNotificationDTO
from application.dtos.technical_task_key_state import TechnicalTaskKeyStateDTO
from application.dtos.technical_task_timeout_notification import TechnicalTaskTimeoutNotificationDTO
from application.dtos.technical_task_review_resolution import TechnicalTaskReviewResolutionDTO
from domain.entities.product_key import ProductKey


class TechnicalTaskRepositoryPort(ABC):
    @abstractmethod
    async def create_technical_task_review(
        self,
        token: str,
        manager_user_id: int,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        submission_text: str,
        business_connection_id: str | None,
    ) -> None: ...

    @abstractmethod
    async def resolve_technical_task_review(
        self, token: str, approved: bool
    ) -> TechnicalTaskReviewResolutionDTO | None: ...

    @abstractmethod
    async def start_technical_task_stage(self, applicant_chat_id: int, task_type: str, max_key_count: int) -> None: ...

    @abstractmethod
    async def start_technical_task_stage_with_connection(
        self,
        applicant_chat_id: int,
        task_type: str,
        max_key_count: int,
        business_connection_id: str | None,
    ) -> None: ...

    @abstractmethod
    async def mark_technical_task_started(self, applicant_chat_id: int) -> None: ...

    @abstractmethod
    async def mark_technical_task_submitted(self, applicant_chat_id: int, submission_text: str) -> None: ...

    @abstractmethod
    async def mark_technical_task_declined(self, applicant_chat_id: int, decline_text: str) -> None: ...

    @abstractmethod
    async def apply_reject_cooldown(self, applicant_chat_id: int) -> None: ...

    @abstractmethod
    async def get_technical_task_key_state(self, applicant_chat_id: int) -> TechnicalTaskKeyStateDTO | None: ...

    @abstractmethod
    async def has_started_technical_task(self, applicant_chat_id: int) -> bool: ...

    @abstractmethod
    async def mark_technical_task_key_issued(self, applicant_chat_id: int) -> None: ...

    @abstractmethod
    async def claim_available_product_key(self, applicant_chat_id: int) -> ProductKey | None: ...

    @abstractmethod
    async def add_product_keys(self, keys: list[ProductKey]) -> int: ...

    @abstractmethod
    async def collect_expired_technical_tasks(self) -> int: ...

    @abstractmethod
    async def get_pending_technical_task_timeout_notifications(self) -> list[TechnicalTaskTimeoutNotificationDTO]: ...

    @abstractmethod
    async def mark_technical_task_timeout_notified(self, applicant_chat_id: int) -> None: ...

    @abstractmethod
    async def get_pending_technical_task_key_logs(self) -> list[TechnicalTaskKeyLogNotificationDTO]: ...

    @abstractmethod
    async def mark_technical_task_key_log_notified(self, log_id: int) -> None: ...

    @abstractmethod
    async def get_low_product_key_alert(self, threshold: int) -> int | None: ...

    @abstractmethod
    async def mark_low_product_key_alert_sent(self, remaining_count: int) -> None: ...

    @abstractmethod
    async def add_pending_chat_acceptance(self, applicant_chat_id: int, applicant_user_id: int, target_chat_id: int) -> None: ...

    @abstractmethod
    async def remove_pending_chat_acceptance(self, applicant_user_id: int, target_chat_id: int) -> bool: ...
