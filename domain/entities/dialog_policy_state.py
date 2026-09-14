from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DialogPolicyState:
    human_takeover: bool
    block_reason: str | None
    block_expires_at: str | None
    technical_task_status: str | None
    last_user_text: str | None
    last_user_at: int | None
