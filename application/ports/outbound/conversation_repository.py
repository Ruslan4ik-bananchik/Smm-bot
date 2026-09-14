from __future__ import annotations

from abc import ABC, abstractmethod
from domain.entities.dialog_policy_state import DialogPolicyState


class ConversationRepositoryPort(ABC):
    @abstractmethod
    async def get_dialog_policy_state(self, dialog_id: int) -> DialogPolicyState: ...

    @abstractmethod
    async def get_dialog_history(self, dialog_id: int, history_limit: int) -> list[str]: ...

    @abstractmethod
    async def store_user_message(self, dialog_id: int, text: str, created_at: int) -> None: ...

    @abstractmethod
    async def mark_human_takeover(self, dialog_id: int) -> None: ...

    @abstractmethod
    async def clear_dialog_block(self, dialog_id: int) -> None: ...

    @abstractmethod
    async def append_message(
        self,
        dialog_id: int,
        text: str,
        auto_close_eligible: bool = False,
        force_auto_close: bool = False,
    ) -> None: ...

    @abstractmethod
    async def close_dialog(self, dialog_id: int) -> None: ...

    @abstractmethod
    async def close_dialog_with_reject_cooldown(self, dialog_id: int) -> None: ...

    @abstractmethod
    async def mark_dialog_as_troll(
        self,
        *,
        dialog_id: int,
        user_id: int,
        username: str | None,
        text: str,
        source_message_link: str | None,
        business_connection_id: str | None,
    ) -> None: ...

    @abstractmethod
    async def upsert_business_connection(self, connection_id: str, owner_user_id: int, is_enabled: bool) -> None: ...

    @abstractmethod
    async def get_business_connection_owner(self, connection_id: str) -> int | None: ...
