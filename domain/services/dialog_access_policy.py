from __future__ import annotations

import re
from datetime import datetime, timezone

from domain.entities.dialog_policy_state import DialogPolicyState
from domain.value_objects.technical_task_code import TechnicalTaskCode


class DialogAccessPolicy:
    DEDUPE_WINDOW_SEC = 25
    APPLICATION_FLOW = "application"
    TECHNICAL_TASK_FLOW = "technical_task"
    TECHNICAL_TASK_FLOW_STATUSES = {"awaiting_consent", "task_started", "key_issued", "submitted"}
    LINK_PATTERN = re.compile(r"(?i)\b(?:https?://|www\.)\S+")

    @classmethod
    def has_active_block(cls, state: DialogPolicyState, now: datetime) -> bool:
        if state.block_reason is None:
            return False
        if state.block_expires_at is None:
            return True

        expires_at = datetime.strptime(state.block_expires_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return expires_at > now

    @classmethod
    def should_clear_expired_block(cls, state: DialogPolicyState, now: datetime) -> bool:
        return state.block_reason is not None and not cls.has_active_block(state, now)

    @classmethod
    def should_allow_during_human_takeover(cls, text: str, technical_task_status: str | None) -> bool:
        if cls.LINK_PATTERN.search(text or "") is not None:
            return True

        if not TechnicalTaskCode.looks_like_key_request(text):
            return False

        return technical_task_status in {"task_started", "key_issued"}

    @classmethod
    def is_duplicate(cls, text: str, last_user_text: str | None, last_user_at: int | None, now_ts: int) -> bool:
        return (
            bool(text)
            and not text.startswith("/")
            and last_user_text == text
            and last_user_at is not None
            and (now_ts - last_user_at) <= cls.DEDUPE_WINDOW_SEC
        )

    @classmethod
    def resolve_response_flow(cls, technical_task_status: str | None) -> str:
        if technical_task_status in cls.TECHNICAL_TASK_FLOW_STATUSES:
            return cls.TECHNICAL_TASK_FLOW
        return cls.APPLICATION_FLOW
