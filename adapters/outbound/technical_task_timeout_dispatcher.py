from __future__ import annotations

from aiogram import Bot

from adapters.inbound.telegram.utils.keyboards import build_block_user_keyboard
from application.ports.outbound.logger_port import LoggerPort
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort


class TechnicalTaskTimeoutDispatcher:
    TIMEOUT_TEXT = "Срок на выполнение тестового задания истек. К сожалению, ты не успел завершить ТЗ вовремя, поэтому заявка закрыта."

    def __init__(
        self,
        bot: Bot,
        repo: TechnicalTaskRepositoryPort,
        logger: LoggerPort,
        review_chat_id: int,
        message_thread_id: int | None,
    ):
        self.bot = bot
        self.repo = repo
        self.logger = logger
        self.review_chat_id = review_chat_id
        self.message_thread_id = message_thread_id

    async def run_once(self) -> None:
        await self.repo.collect_expired_technical_tasks()
        notifications = await self.repo.get_pending_technical_task_timeout_notifications()
        for notification in notifications:
            try:
                await self.bot.send_message(
                    chat_id=self.review_chat_id,
                    message_thread_id=self.message_thread_id,
                    text=self._build_manager_text(
                        applicant_chat_id=notification.applicant_chat_id,
                        applicant_user_id=notification.applicant_user_id,
                        applicant_username=notification.applicant_username,
                        task_type=notification.task_type,
                        timed_out_at=notification.timed_out_at,
                        product_key=notification.product_key,
                        key_count=notification.key_count,
                    ),
                    reply_markup=(
                        build_block_user_keyboard(notification.applicant_user_id)
                        if notification.applicant_user_id is not None
                        else None
                    ),
                )
            except Exception as exc:
                self.logger.warning(
                    "Failed to publish technical task timeout log "
                    f"chat_id={notification.applicant_chat_id} "
                    f"error={exc}"
                )
                continue

            if notification.business_connection_id:
                try:
                    await self.bot.send_message(
                        chat_id=notification.applicant_chat_id,
                        business_connection_id=notification.business_connection_id,
                        text=self.TIMEOUT_TEXT,
                    )
                except Exception as exc:
                    self.logger.warning(
                        "Failed to send technical task timeout notification "
                        f"chat_id={notification.applicant_chat_id} "
                        f"connection_id={notification.business_connection_id} "
                        f"error={exc}"
                    )

            await self.repo.mark_technical_task_timeout_notified(notification.applicant_chat_id)

    @staticmethod
    def _build_manager_text(
        *,
        applicant_chat_id: int,
        applicant_user_id: int | None,
        applicant_username: str | None,
        task_type: str,
        timed_out_at: str,
        product_key: str | None,
        key_count: int,
    ) -> str:
        task_label = "Длинные видео" if task_type == "longform" else "Shorts / TikTok"
        key_label = product_key or "не выдавался"
        username_text = f"@{applicant_username}" if applicant_username else "не указан"
        user_id_text = str(applicant_user_id) if applicant_user_id is not None else "не найден"
        profile_text = f"tg://user?id={applicant_user_id}" if applicant_user_id is not None else "не найден"
        return (
            "Просрочено тестовое задание\n\n"
            f"Username: {username_text}\n"
            f"User ID: {user_id_text}\n"
            f"Профиль: {profile_text}\n"
            f"User chat id: {applicant_chat_id}\n"
            f"Формат ТЗ: {task_label}\n"
            f"Время просрочки: {timed_out_at}\n\n"
            "Информация по ключу DLC Umbrella:\n"
            f"- Ключ: {key_label}\n"
            f"- Кол-во выдач: {key_count}"
        )
