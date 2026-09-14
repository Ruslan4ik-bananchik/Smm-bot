from __future__ import annotations

from aiogram.types import Message


def source_message_link(message: Message) -> str | None:
    if not message.chat or not message.chat.username or not message.message_id:
        return None
    return f"https://t.me/{message.chat.username}/{message.message_id}"
