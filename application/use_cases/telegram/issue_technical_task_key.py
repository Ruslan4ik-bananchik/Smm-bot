from __future__ import annotations

from datetime import timezone

from application.dtos.technical_task_key_view import TechnicalTaskKeyViewDTO
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.exceptions.errors import ProductKeyPoolEmptyError, UnhandledException
from domain.services.technical_task_key_policy import TechnicalTaskKeyPolicy
from infra.tz_clock import TZClock


class IssueTechnicalTaskKey:
    def __init__(self, repo: TechnicalTaskRepositoryPort, tz_clock: TZClock):
        self.repo = repo
        self.tz_clock = tz_clock

    async def execute(self, applicant_chat_id: int) -> TechnicalTaskKeyViewDTO:
        state = await self.repo.get_technical_task_key_state(applicant_chat_id)
        if state is None or state.status not in {"task_started", "key_issued"}:
            raise UnhandledException()
        if state.product_key is None:
            claimed_product_key = await self.repo.claim_available_product_key(applicant_chat_id)
            if claimed_product_key is None:
                raise ProductKeyPoolEmptyError()
            state = await self.repo.get_technical_task_key_state(applicant_chat_id)
            if state is None:
                raise UnhandledException()
            product_key = claimed_product_key
        else:
            product_key = state.product_key

        now_utc = self.tz_clock.now().astimezone(timezone.utc)
        is_repeat = TechnicalTaskKeyPolicy.check_can_issue(
            has_product_key=True,
            key_count=state.key_count,
            max_issues=state.max_key_count,
            last_key_time=state.last_key_time,
            now=now_utc,
        )

        await self.repo.mark_technical_task_key_issued(applicant_chat_id)
        return TechnicalTaskKeyViewDTO(value=str(product_key), is_repeat=is_repeat)
