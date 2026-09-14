from __future__ import annotations

from application.dtos.processed_incoming_message import ProcessedIncomingMessageDTO
from application.ports.outbound.conversation_repository import ConversationRepositoryPort
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from application.use_cases.telegram.activate_technical_task import ActivateTechnicalTask
from application.use_cases.telegram.issue_technical_task_key import IssueTechnicalTaskKey
from application.use_cases.telegram.prepare_application_review_dispatch import (
    PrepareApplicationReviewDispatch,
)
from application.use_cases.telegram.prepare_technical_task_decline_dispatch import (
    PrepareTechnicalTaskDeclineDispatch,
)
from application.use_cases.telegram.prepare_technical_task_review_dispatch import (
    PrepareTechnicalTaskReviewDispatch,
)
from application.use_cases.telegram.prepare_troll_report_dispatch import PrepareTrollReportDispatch
from application.use_cases.telegram.request_incoming_message_answer import (
    RequestIncomingMessageAnswer,
)
from domain.exceptions.errors import ApplicationRetakeAfterTechnicalTaskStartError
from domain.services.technical_task_submission_policy import TechnicalTaskSubmissionPolicy


class ProcessIncomingMessage:
    def __init__(
        self,
        request_incoming_message_answer: RequestIncomingMessageAnswer,
        activate_technical_task: ActivateTechnicalTask,
        issue_technical_task_key: IssueTechnicalTaskKey,
        prepare_application_review_dispatch: PrepareApplicationReviewDispatch,
        prepare_technical_task_review_dispatch: PrepareTechnicalTaskReviewDispatch,
        prepare_technical_task_decline_dispatch: PrepareTechnicalTaskDeclineDispatch,
        prepare_troll_report_dispatch: PrepareTrollReportDispatch,
        conversation_repo: ConversationRepositoryPort,
        technical_task_repo: TechnicalTaskRepositoryPort,
    ):
        self.request_incoming_message_answer = request_incoming_message_answer
        self.activate_technical_task = activate_technical_task
        self.issue_technical_task_key = issue_technical_task_key
        self.prepare_application_review_dispatch = prepare_application_review_dispatch
        self.prepare_technical_task_review_dispatch = prepare_technical_task_review_dispatch
        self.prepare_technical_task_decline_dispatch = prepare_technical_task_decline_dispatch
        self.prepare_troll_report_dispatch = prepare_troll_report_dispatch
        self.conversation_repo = conversation_repo
        self.technical_task_repo = technical_task_repo

    async def execute(
        self,
        *,
        user_id: int,
        dialog_id: int,
        text: str,
        history: list[str],
        response_flow: str,
        business_connection_id: str | None,
        applicant_username: str | None,
        source_message_link: str | None,
    ) -> ProcessedIncomingMessageDTO:
        result = await self.request_incoming_message_answer.execute(
            user_id=user_id,
            text=text,
            history=history,
            flow=response_flow,
        )

        if result.should_activate_technical_task:
            await self.activate_technical_task.execute(dialog_id)

        technical_task_key = None
        if result.should_issue_product_key:
            state = await self.technical_task_repo.get_technical_task_key_state(dialog_id)
            if state is not None and state.status in {"task_started", "key_issued"}:
                technical_task_key = await self.issue_technical_task_key.execute(dialog_id)

        review_dispatch = None
        if result.application_form is not None:
            if await self.technical_task_repo.has_started_technical_task(dialog_id):
                raise ApplicationRetakeAfterTechnicalTaskStartError()
            review_dispatch = await self.prepare_application_review_dispatch.execute(
                result=result,
                applicant_user_id=user_id,
                applicant_chat_id=dialog_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                business_connection_id=business_connection_id,
            )

        technical_task_review_dispatch = None
        if result.should_complete_technical_task:
            state = await self.technical_task_repo.get_technical_task_key_state(dialog_id)
            TechnicalTaskSubmissionPolicy.ensure_valid_submission(
                text=text,
                task_type=state.task_type if state is not None else None,
            )
            technical_task_review_dispatch = await self.prepare_technical_task_review_dispatch.execute(
                applicant_user_id=user_id,
                applicant_chat_id=dialog_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                submission_text=text,
                business_connection_id=business_connection_id,
            )

        technical_task_decline_dispatch = None
        if result.should_decline_technical_task:
            state = await self.technical_task_repo.get_technical_task_key_state(dialog_id)
            await self.technical_task_repo.mark_technical_task_declined(dialog_id, text)
            await self.conversation_repo.close_dialog_with_reject_cooldown(dialog_id)
            technical_task_decline_dispatch = self.prepare_technical_task_decline_dispatch.execute(
                applicant_user_id=user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                decline_text=text,
                product_key=str(state.product_key) if state is not None and state.product_key is not None else None,
                key_count=state.key_count if state is not None else 0,
            )

        troll_report_dispatch = None
        if result.should_block_as_troll:
            await self.conversation_repo.mark_dialog_as_troll(
                dialog_id=dialog_id,
                user_id=user_id,
                username=applicant_username,
                text=text,
                source_message_link=source_message_link,
                business_connection_id=business_connection_id,
            )
            troll_report_dispatch = self.prepare_troll_report_dispatch.execute(
                applicant_user_id=user_id,
                applicant_username=applicant_username,
                source_message_link=source_message_link,
                troll_text=text,
            )

        if result.should_auto_close:
            if review_dispatch is None:
                await self.conversation_repo.close_dialog_with_reject_cooldown(dialog_id)

        await self.conversation_repo.append_message(
            dialog_id,
            result.text,
            auto_close_eligible=True,
            force_auto_close=False,
        )
        return ProcessedIncomingMessageDTO(
            reply_text=result.text,
            review_dispatch=review_dispatch,
            technical_task_review_dispatch=technical_task_review_dispatch,
            technical_task_decline_dispatch=technical_task_decline_dispatch,
            troll_report_dispatch=troll_report_dispatch,
            technical_task_key=technical_task_key,
        )
