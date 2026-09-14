from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import BaseMiddleware, Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy


class TelegramBotInfra:
    def __init__(self, tg_bot_token: str, storage: Optional[MemoryStorage] = None, fsm_strategy: FSMStrategy = FSMStrategy.GLOBAL_USER):
        self.bot = Bot(token=tg_bot_token)
        self.dp = Dispatcher(storage=storage or MemoryStorage(), fsm_strategy=fsm_strategy)
        self._polling_task: Optional[asyncio.Task[None]] = None

    def attach_router(self, router: Router) -> None:
        self.dp.include_router(router)

    def attach_outer_at_message(self, middleware: BaseMiddleware) -> None:
        self.dp.message.outer_middleware(middleware)

    def attach_outer_at_business_message(self, middleware: BaseMiddleware) -> None:
        self.dp.business_message.outer_middleware(middleware)

    def attach_outer_at_edited_business_message(self, middleware: BaseMiddleware) -> None:
        self.dp.edited_business_message.outer_middleware(middleware)

    def attach_outer_at_business_connection(self, middleware: BaseMiddleware) -> None:
        self.dp.business_connection.outer_middleware(middleware)

    def attach_outer_at_callback_query(self, middleware: BaseMiddleware) -> None:
        self.dp.callback_query.outer_middleware(middleware)

    def attach_outer_at_chat_member(self, middleware: BaseMiddleware) -> None:
        self.dp.chat_member.outer_middleware(middleware)

    def attach_outer_at_chat_join_request(self, middleware: BaseMiddleware) -> None:
        self.dp.chat_join_request.outer_middleware(middleware)

    async def start_polling(self) -> None:
        if self._polling_task and not self._polling_task.done():
            return

        await self.bot.get_me()
        allowed_updates = self.dp.resolve_used_update_types()
        polling_coro = self.dp.start_polling(  # pyright: ignore[reportUnknownMemberType]
            self.bot,
            allowed_updates=allowed_updates,
            handle_signals=False,
        )

        self._polling_task = asyncio.create_task(polling_coro)

    async def stop_polling(self) -> None:
        if self._polling_task:
            if not self._polling_task.done():
                await self.dp.stop_polling()
            await asyncio.gather(self._polling_task, return_exceptions=True)
            self._polling_task = None

        await self.bot.session.close()
