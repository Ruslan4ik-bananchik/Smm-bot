from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from application.dtos.application_review_callback_result import ApplicationReviewCallbackResultDTO
from application.dtos.technical_task_review_callback_result import TechnicalTaskReviewCallbackResultDTO
from domain.services.technical_task_profile import TechnicalTaskProfileResolver


def build_application_review_callback_user_text(result: ApplicationReviewCallbackResultDTO) -> str:
    if result.status == "approved":
        if result.technical_task_text:
            return result.technical_task_text
        profile = TechnicalTaskProfileResolver.resolve(result.video_format_code)
        return profile.task_text
    return "Твоя заявка отклонена. Спасибо за интерес. \n Следующую заявку можно подать через 4 дня."


def build_application_review_callback_status_text(result: ApplicationReviewCallbackResultDTO) -> str:
    if result.status == "approved":
        return "Принято"
    return "Отклонено"


def build_application_review_callback_alert_text(result: ApplicationReviewCallbackResultDTO) -> str:
    return "Решение сохранено"


def build_technical_task_callback_user_text(
    result: TechnicalTaskReviewCallbackResultDTO,
    chat_link: str | None,
) -> str:
    if result.status == "approved":
        if chat_link:
            return f"Менеджер принял твое тестовое задание. Отправь заявку в данный чат {chat_link}"
        return "Менеджер принял твое тестовое задание. Дальше с тобой свяжется менеджер."
    return "Тестовое задание отклонено. Спасибо за проделанную работу.\n Следующую заявку на вступление можно подать через 4 дня."


def build_technical_task_callback_status_text(result: TechnicalTaskReviewCallbackResultDTO) -> str:
    if result.status == "approved":
        return "ТЗ принято"
    return "ТЗ отклонено"


def build_technical_task_callback_alert_text(result: TechnicalTaskReviewCallbackResultDTO) -> str:
    return "Решение по ТЗ сохранено"


def parse_callback_user_id(raw_payload: str | None, prefix: str) -> int:
    parts = (raw_payload or "").split(":", 1)
    if len(parts) != 2 or parts[0] != prefix:
        raise ValueError("invalid_callback_payload")
    return int(parts[1])


async def publish_manager_review_status(callback: CallbackQuery, status_text: str) -> None:
    if not isinstance(callback.message, Message):
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(f"Статус заявки: {status_text}")
