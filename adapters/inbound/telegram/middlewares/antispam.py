from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from application.ports.outbound.logger_port import LoggerPort


class AntiSpamMiddleware(BaseMiddleware):
    RATE_LIMIT = 1  
    TIME_WINDOW = 13.0
    RESPONSE_DELAY = 1.5

    def __init__(self, logger: LoggerPort, manager_user_id: int) -> None:
        self.logger = logger
        self.manager = manager_user_id
        self.user_timestamps: dict[int, list[float]] = defaultdict(list)
        self.user_last_response: dict[int, float] = {}
        self.tag = "AntiSpamMiddleware"

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()

        timestamps = [ts for ts in self.user_timestamps[user_id] if now - ts <= self.TIME_WINDOW]
        timestamps.append(now)
        self.user_timestamps[user_id] = timestamps

        last_response = self.user_last_response.get(user_id, 0.0)
        if len(timestamps) > self.RATE_LIMIT and now - last_response < self.RESPONSE_DELAY and self.manager != user_id:
            self.logger.info(f"{self.tag} Rate limit hit for user {user_id}, ignoring call")
            return None

        self.user_last_response[user_id] = now
        return await handler(event, data)
