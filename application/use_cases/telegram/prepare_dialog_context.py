from __future__ import annotations

import time
from datetime import datetime, timezone

from application.dtos.dialog_context import DialogContextDTO
from application.ports.outbound.conversation_repository import ConversationRepositoryPort
from domain.services.dialog_access_policy import DialogAccessPolicy


class PrepareDialogContext:
    HISTORY_LIMIT = 5

    def __init__(self, repo: ConversationRepositoryPort):
        self.repo = repo

    async def execute(self, dialog_id: int, user_id: int, text: str, business_connection_id: str | None) -> DialogContextDTO:
        if business_connection_id:
            connection_owner = await self.repo.get_business_connection_owner(business_connection_id)
            if connection_owner == user_id:
                await self.repo.mark_human_takeover(dialog_id)
                return DialogContextDTO(
                    should_process=False,
                    history=[],
                    response_flow=DialogAccessPolicy.APPLICATION_FLOW,
                )

        state = await self.repo.get_dialog_policy_state(dialog_id)
        now = datetime.now(timezone.utc)
        if DialogAccessPolicy.should_clear_expired_block(state, now):
            await self.repo.clear_dialog_block(dialog_id)
            state = await self.repo.get_dialog_policy_state(dialog_id)

        if DialogAccessPolicy.has_active_block(state, now):
            return DialogContextDTO(
                should_process=False,
                history=[],
                response_flow=DialogAccessPolicy.APPLICATION_FLOW,
            )

        if state.human_takeover and not DialogAccessPolicy.should_allow_during_human_takeover(text, state.technical_task_status):
            return DialogContextDTO(
                should_process=False,
                history=[],
                response_flow=DialogAccessPolicy.APPLICATION_FLOW,
            )

        now_ts = int(time.time())
        if DialogAccessPolicy.is_duplicate(text, state.last_user_text, state.last_user_at, now_ts):
            return DialogContextDTO(
                should_process=False,
                history=[],
                response_flow=DialogAccessPolicy.APPLICATION_FLOW,
            )

        history = await self.repo.get_dialog_history(dialog_id, self.HISTORY_LIMIT)
        response_flow = DialogAccessPolicy.resolve_response_flow(state.technical_task_status)

        if text:
            await self.repo.store_user_message(dialog_id, text, now_ts)

        return DialogContextDTO(
            should_process=True,
            history=history,
            response_flow=response_flow,
        )
