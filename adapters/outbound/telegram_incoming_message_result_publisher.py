from __future__ import annotations

from aiogram import Bot

from adapters.inbound.telegram.utils.keyboards import build_block_user_keyboard, build_review_keyboard
from adapters.inbound.telegram.utils.review_texts import (
    build_application_review_text,
    build_processed_reply_text,
    build_technical_task_decline_text,
    build_technical_task_review_text,
    build_troll_report_text,
)
from application.dtos.application_review_dispatch import ApplicationReviewDispatchDTO
from application.dtos.processed_incoming_message import ProcessedIncomingMessageDTO
from application.dtos.technical_task_decline_dispatch import TechnicalTaskDeclineDispatchDTO
from application.dtos.technical_task_review_dispatch import TechnicalTaskReviewDispatchDTO
from application.dtos.troll_report_dispatch import TrollReportDispatchDTO
from application.ports.outbound.incoming_message_result_publisher import IncomingMessageResultPublisherPort
from application.ports.outbound.logger_port import LoggerPort


class TelegramIncomingMessageResultPublisher(IncomingMessageResultPublisherPort):
    def __init__(self, bot: Bot, logger: LoggerPort):
        self.bot = bot
        self.logger = logger

    async def publish_reply(
        self,
        result: ProcessedIncomingMessageDTO,
        *,
        chat_id: int,
        business_connection_id: str | None,
    ) -> None:
        reply_text = build_processed_reply_text(result)
        if not reply_text:
            return

        await self.bot.send_message(
            chat_id=chat_id,
            text=reply_text,
            business_connection_id=business_connection_id,
        )

    async def publish_application_review(self, dispatch: ApplicationReviewDispatchDTO | None) -> None:
        if dispatch is None:
            return

        keyboard = build_review_keyboard(
            approve_data=dispatch.approve_callback_data,
            reject_data=dispatch.reject_callback_data,
        )
        try:
            await self.bot.send_message(
                chat_id=dispatch.review_chat_id,
                message_thread_id=dispatch.message_thread_id,
                text=build_application_review_text(dispatch.view_data),
                reply_markup=keyboard,
            )
            self.logger.info(
                f"Manager review sent chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id}"
            )
        except Exception as exc:
            self.logger.error(
                "Failed to submit manager review "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id} error={exc}"
            )

    async def publish_technical_task_review(self, dispatch: TechnicalTaskReviewDispatchDTO | None) -> bool:
        if dispatch is None:
            return False

        try:
            await self.bot.send_message(
                chat_id=dispatch.review_chat_id,
                message_thread_id=dispatch.message_thread_id,
                text=build_technical_task_review_text(dispatch.view_data),
                reply_markup=build_review_keyboard(
                    approve_data=dispatch.approve_callback_data,
                    reject_data=dispatch.reject_callback_data,
                ),
            )
            self.logger.info(
                "Technical task review sent "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id}"
            )
            return True
        except Exception as exc:
            self.logger.error(
                "Failed to submit technical task review "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id} error={exc}"
            )
            return False

    async def publish_technical_task_decline(self, dispatch: TechnicalTaskDeclineDispatchDTO | None) -> None:
        if dispatch is None:
            return

        try:
            await self.bot.send_message(
                chat_id=dispatch.review_chat_id,
                message_thread_id=dispatch.message_thread_id,
                text=build_technical_task_decline_text(dispatch.view_data),
                reply_markup=build_block_user_keyboard(dispatch.view_data.applicant_user_id),
            )
            self.logger.info(
                "Technical task decline sent "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id}"
            )
        except Exception as exc:
            self.logger.error(
                "Failed to submit technical task decline "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id} error={exc}"
            )

    async def publish_troll_report(self, dispatch: TrollReportDispatchDTO | None) -> None:
        if dispatch is None:
            return

        try:
            await self.bot.send_message(
                chat_id=dispatch.review_chat_id,
                message_thread_id=dispatch.message_thread_id,
                text=build_troll_report_text(dispatch.view_data),
                reply_markup=build_block_user_keyboard(dispatch.view_data.applicant_user_id),
            )
            self.logger.info(
                f"Troll report sent chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id}"
            )
        except Exception as exc:
            self.logger.error(
                "Failed to submit troll report "
                f"chat={dispatch.review_chat_id} applicant={dispatch.view_data.applicant_user_id} error={exc}"
            )
