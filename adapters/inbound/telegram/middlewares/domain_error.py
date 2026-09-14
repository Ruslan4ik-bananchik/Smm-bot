from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from adapters.inbound.telegram.utils.errors_i18n import get_error_message
from application.ports.outbound.logger_port import LoggerPort
from domain.exceptions.errors import DomainError


class DomainErrorMiddleware(BaseMiddleware):
    def __init__(self, logger: LoggerPort) -> None:
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except DomainError as exc:
            text_out = get_error_message(exc.code)

            if isinstance(event, Message):
                await event.answer(text_out)
                sender_id = event.from_user.id if event.from_user else None
                username = f"@{event.from_user.username}" if event.from_user and event.from_user.username else None
                raw_text = event.text or event.caption or ""
                payload = raw_text if len(raw_text) <= 300 else f"{raw_text[:300]}..."
                self.logger.error(
                    "DomainError caught "
                    f"error={exc.__class__.__name__} "
                    f"code={exc.code} "
                    f"sender_id={sender_id} "
                    f"username={username} "
                    f"message={payload}"
                )
                return None

            if isinstance(event, CallbackQuery):
                await event.answer(text_out, show_alert=True)
                sender_id = event.from_user.id if event.from_user else None
                username = f"@{event.from_user.username}" if event.from_user and event.from_user.username else None
                payload = event.data or ""
                self.logger.error(
                    "DomainError caught "
                    f"error={exc.__class__.__name__} "
                    f"code={exc.code} "
                    f"sender_id={sender_id} "
                    f"username={username} "
                    f"callback_data={payload}"
                )
                return None

            self.logger.error(
                "DomainError caught "
                f"error={exc.__class__.__name__} code={exc.code}"
            )
            return None
