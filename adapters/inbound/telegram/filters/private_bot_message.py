from __future__ import annotations

from aiogram.filters import Filter
from aiogram.types import Message

from application.ports.inbound.app_actions_port import AppActionsPort


class PrivateBotMessageAccessFilter(Filter):
    async def __call__(self, message: Message, actions: AppActionsPort) -> bool:
        if message.chat.type != "private":
            return False
        if message.business_connection_id is not None:
            return False
        if message.from_user is None:
            return False
        await actions.access_check.execute(message.from_user.id)
        return True
