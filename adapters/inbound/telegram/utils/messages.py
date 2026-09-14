from __future__ import annotations

from io import BytesIO

from aiogram import Bot
from aiogram.types import BotCommand, Document

from domain.exceptions.errors import BannerFileExpectedError, ProductKeyFileExpectedError, ProductKeyFileInvalidError


def ensure_txt_document(document: Document | None) -> Document:
    if document is None:
        raise ProductKeyFileExpectedError()
    if not (document.file_name or "").lower().endswith(".txt"):
        raise ProductKeyFileExpectedError()
    return document


async def read_txt_document(bot: Bot | None, document: Document) -> str:
    if bot is None:
        raise ProductKeyFileInvalidError()

    buffer = BytesIO()
    await bot.download(document, destination=buffer)
    try:
        return buffer.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProductKeyFileInvalidError() from exc


def ensure_banner_document(document: Document | None) -> Document:
    if document is None:
        raise BannerFileExpectedError()
    return document


def default_menu_commands() -> list[BotCommand]:
    return [
        BotCommand(command="help", description="помощь"),
    ]


def manager_menu_commands() -> list[BotCommand]:
    return [
        BotCommand(command="help", description="список команд"),
        BotCommand(command="upload_keys", description="загрузить ключи"),
        BotCommand(command="upload_banner", description="загрузить баннер"),
        BotCommand(command="banner", description="получить баннер"),
        BotCommand(command="set_link", description="задать ссылку чата"),
        BotCommand(command="set_link_chat_id", description="задать chat_id чата"),
        BotCommand(command="ban", description="заблокировать по user_id"),
        BotCommand(command="unban", description="снять бан по user_id"),
    ]


def help_commands() -> str:
    return (
        "/upload_keys -> загрузить ключи (state) .txt\n"
        "/upload_banner -> загрузить баннер (state) любой формат\n"
        "/banner -> получить текущий баннер\n"
        "/set_link -> задать ссылку на чат\n"
        "/set_link_chat_id -> задать chat_id чата ожидания\n"
        "/ban ID человека -> забанить человека по ID в телеграмме\n"
        "/unban ID человека -> снять вечный бан по ID в телеграмме"
    )
