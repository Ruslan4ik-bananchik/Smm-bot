from __future__ import annotations

from aiogram import Bot

from application.ports.outbound.logger_port import LoggerPort
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort


class TechnicalTaskKeyLogDispatcher:
    LOW_STOCK_THRESHOLD = 10

    def __init__(
        self,
        bot: Bot,
        repo: TechnicalTaskRepositoryPort,
        logger: LoggerPort,
        review_chat_id: int,
        message_thread_id: int | None,
        low_stock_thread_id: int | None,
    ):
        self.bot = bot
        self.repo = repo
        self.logger = logger
        self.review_chat_id = review_chat_id
        self.message_thread_id = message_thread_id
        self.low_stock_thread_id = low_stock_thread_id

    async def run_once(self) -> None:
        notifications = await self.repo.get_pending_technical_task_key_logs()
        for notification in notifications:
            try:
                await self.bot.send_message(
                    chat_id=self.review_chat_id,
                    message_thread_id=self.message_thread_id,
                    text=self._build_text(
                        applicant_chat_id=notification.applicant_chat_id,
                        applicant_user_id=notification.applicant_user_id,
                        applicant_username=notification.applicant_username,
                        event_type=notification.event_type,
                        event_data=notification.event_data,
                        created_at=notification.created_at,
                    ),
                )
                await self.repo.mark_technical_task_key_log_notified(notification.log_id)
            except Exception as exc:
                self.logger.warning(
                    "Failed to publish technical task key log "
                    f"log_id={notification.log_id} "
                    f"chat_id={notification.applicant_chat_id} "
                    f"error={exc}"
                )
        await self._notify_low_stock_if_needed()

    async def _notify_low_stock_if_needed(self) -> None:
        if self.low_stock_thread_id is None:
            return

        remaining_count = await self.repo.get_low_product_key_alert(self.LOW_STOCK_THRESHOLD)
        if remaining_count is None:
            return

        try:
            await self.bot.send_message(
                chat_id=self.review_chat_id,
                message_thread_id=self.low_stock_thread_id,
                text=(
                    "Внимание: ключей осталось меньше 10.\n\n"
                    f"Остаток свободных ключей: {remaining_count}"
                ),
            )
            await self.repo.mark_low_product_key_alert_sent(remaining_count)
        except Exception as exc:
            self.logger.warning(
                "Failed to publish low product key stock alert "
                f"remaining_count={remaining_count} "
                f"error={exc}"
            )

    @staticmethod
    def _build_text(
        *,
        applicant_chat_id: int,
        applicant_user_id: int | None,
        applicant_username: str | None,
        event_type: str,
        event_data: str | None,
        created_at: str,
    ) -> str:
        title = {
            "key_reserved": "Зарезервирован ключ DLC Umbrella",
            "key_issued": "Выдан ключ DLC Umbrella",
        }.get(event_type, "Событие по ключу DLC Umbrella")
        username_text = f"@{applicant_username}" if applicant_username else "не указан"
        user_id_text = str(applicant_user_id) if applicant_user_id is not None else "не найден"
        profile_text = f"tg://user?id={applicant_user_id}" if applicant_user_id is not None else "не найден"
        lines = [
            title,
            "",
            f"Username: {username_text}",
            f"User ID: {user_id_text}",
            f"Профиль: {profile_text}",
            f"User chat id: {applicant_chat_id}",
            f"Событие: {event_type}",
            f"Время: {created_at}",
        ]
        if event_data:
            lines.append(f"Данные: {event_data}")
        return "\n".join(lines)
