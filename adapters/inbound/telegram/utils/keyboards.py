from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from adapters.inbound.telegram.storage.emoji_ids import (
    APPROVE_ICON_EMOJI_ID,
    BLOCK_ICON_EMOJI_ID,
    REJECT_ICON_EMOJI_ID,
)


def build_review_keyboard(approve_data: str, reject_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Принять",
            callback_data=approve_data,
            style="success",
            icon_custom_emoji_id=APPROVE_ICON_EMOJI_ID,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отклонить",
            callback_data=reject_data,
            style="danger",
            icon_custom_emoji_id=REJECT_ICON_EMOJI_ID,
        )
    )
    return builder.as_markup()


def build_block_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Заблокировать",
            callback_data=f"block_user:{user_id}",
            style="primary",
            icon_custom_emoji_id=BLOCK_ICON_EMOJI_ID,
        )
    )
    return builder.as_markup()
