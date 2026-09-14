from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import BusinessConnection, Message, TelegramObject

from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort


class DomainContextMiddleware(BaseMiddleware):
    def __init__(self, app_actions: AppActionsPort, logger: LoggerPort) -> None:
        self.app_actions = app_actions
        self.logger = logger
        self.tag = "DomainContextMiddleware"

    async def _sync_business_connection(self, bot: Bot, connection_id: str) -> None:
        connection = await bot.get_business_connection(connection_id)
        await self.app_actions.update_business_connection.execute(
            connection_id=connection.id,
            owner_user_id=connection.user.id,
            is_enabled=connection.is_enabled,
        )

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: dict[str, Any]) -> Any:
        data["actions"] = self.app_actions
        data["logger"] = self.logger
        
        if isinstance(event, BusinessConnection):
            await self.app_actions.update_business_connection.execute(connection_id=event.id, owner_user_id=event.user.id, is_enabled=event.is_enabled)
            return await handler(event, data)

        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id
        dialog_id = event.chat.id if event.chat else user_id
        text = (event.text or event.caption or "").strip()
        business_connection_id = event.business_connection_id

        if await self.app_actions.is_blocked_in_blocklist.execute(user_id):
            self.logger.info(f"{self.tag} Skipping blocked user user_id={user_id}")
            return None

        if business_connection_id:
            bot = data.get("bot")
            if isinstance(bot, Bot):
                try:
                    await self._sync_business_connection(bot, business_connection_id)
                except Exception as exc:
                    self.logger.warning(
                        f"{self.tag} Failed to sync business connection "
                        f"connection_id={business_connection_id} error={exc}"
                    )
            is_allowed_connection = await self.app_actions.validate_business_connection.execute(business_connection_id)
            if not is_allowed_connection:
                self.logger.info(
                    f"{self.tag} Skipping message by business connection policy "
                    f"connection_id={business_connection_id} user_id={user_id}"
                )
                return None

        context = await self.app_actions.prepare_dialog_context.execute(dialog_id=dialog_id, user_id=user_id, text=text, business_connection_id=business_connection_id)

        if not context.should_process:
            self.logger.info(f"{self.tag} Skipping message by dialog policy " f"dialog_id={dialog_id} user_id={user_id}")
            return None

        data["user_id"] = user_id
        data["dialog_id"] = dialog_id
        data["history"] = context.history
        data["response_flow"] = context.response_flow
        data["business_connection_id"] = business_connection_id

        self.logger.info(f"{self.tag} Handling message from user {user_id}")
        return await handler(event, data)
