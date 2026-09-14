from __future__ import annotations

from application.dtos.application_review_view_data import ApplicationReviewViewDataDTO
from application.dtos.processed_incoming_message import ProcessedIncomingMessageDTO
from application.dtos.technical_task_decline_view_data import TechnicalTaskDeclineViewDataDTO
from application.dtos.technical_task_review_view_data import TechnicalTaskReviewViewDataDTO
from application.dtos.troll_report_view_data import TrollReportViewDataDTO


def build_application_review_text(view_data: ApplicationReviewViewDataDTO) -> str:
    username_text = f"@{view_data.applicant_username}" if view_data.applicant_username else "не указан"
    user_link = f"tg://user?id={view_data.applicant_user_id}"
    form = view_data.application_form

    header_lines = [
        "Новая заявка\n",
        f"Username: {username_text}",
        f"User ID: {view_data.applicant_user_id}",
        f"Профиль: {user_link}",
    ]
    if view_data.source_message_link:
        header_lines.append(f"Ссылка на сообщение: {view_data.source_message_link}")

    form_lines = [
        "",
        f"- Монтаж: {form.montage}",
        f"- Опыт: {form.experience}",
        f"- Игра: {form.game}",
        f"- Канал: {form.channel}",
        f"- Формат: {form.video_format}",
    ]
    return "\n".join(header_lines + form_lines)


def build_technical_task_review_text(view_data: TechnicalTaskReviewViewDataDTO) -> str:
    username_text = f"@{view_data.applicant_username}" if view_data.applicant_username else "не указан"
    user_link = f"tg://user?id={view_data.applicant_user_id}"

    lines = [
        "Тестовое задание завершено\n",
        f"Username: {username_text}",
        f"User ID: {view_data.applicant_user_id}",
        f"Профиль: {user_link}",
    ]
    if view_data.source_message_link:
        lines.append(f"Ссылка на сообщение: {view_data.source_message_link}")
    lines.extend(
        [
            "",
            "Ссылки/материалы от кандидата:",
            view_data.submission_text,
        ]
    )
    return "\n".join(lines)


def build_technical_task_decline_text(view_data: TechnicalTaskDeclineViewDataDTO) -> str:
    username_text = f"@{view_data.applicant_username}" if view_data.applicant_username else "не указан"
    user_link = f"tg://user?id={view_data.applicant_user_id}"
    key_label = view_data.product_key or "не выдавался"

    lines = [
        "Кандидат отказался от тестового задания\n",
        f"Username: {username_text}",
        f"User ID: {view_data.applicant_user_id}",
        f"Профиль: {user_link}",
    ]
    if view_data.source_message_link:
        lines.append(f"Ссылка на сообщение: {view_data.source_message_link}")
    lines.extend(
        [
            "",
            "Сообщение кандидата:",
            view_data.decline_text,
            "",
            "Информация по ключу DLC Umbrella:",
            f"- Ключ: {key_label}",
            f"- Кол-во выдач: {view_data.key_count}",
        ]
    )
    return "\n".join(lines)


def build_troll_report_text(view_data: TrollReportViewDataDTO) -> str:
    username_text = f"@{view_data.applicant_username}" if view_data.applicant_username else "не указан"
    user_link = f"tg://user?id={view_data.applicant_user_id}"

    lines = [
        "Обнаружен тролль\n",
        f"Username: {username_text}",
        f"User ID: {view_data.applicant_user_id}",
        f"Профиль: {user_link}",
    ]
    if view_data.source_message_link:
        lines.append(f"Ссылка на сообщение: {view_data.source_message_link}")
    lines.extend(
        [
            "",
            "Сообщение кандидата:",
            view_data.troll_text,
        ]
    )
    return "\n".join(lines)


def build_processed_reply_text(result: ProcessedIncomingMessageDTO) -> str:
    key_view = result.technical_task_key
    if key_view is None:
        return result.reply_text
    prefix = "Повторно отправляю ключ." if key_view.is_repeat else "Отправляю ключ."
    return f"{prefix}\n\nТвой ключ: {key_view.value}"
