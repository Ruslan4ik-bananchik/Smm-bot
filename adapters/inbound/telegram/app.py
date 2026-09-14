from __future__ import annotations

from aiogram.types import BotCommandScopeAllPrivateChats, BotCommandScopeChat

from adapters.inbound.telegram.handlers.business import router as business_router
from adapters.inbound.telegram.handlers.chat_members import router as chat_members_router
from adapters.inbound.telegram.handlers.messages import router as messages_router
from adapters.inbound.telegram.handlers.reviews import router as reviews_router
from adapters.inbound.telegram.middlewares.antispam import AntiSpamMiddleware
from adapters.inbound.telegram.middlewares.domain_context import DomainContextMiddleware
from adapters.inbound.telegram.middlewares.domain_error import DomainErrorMiddleware
from adapters.inbound.telegram.states.banner_upload_handler import router as banner_upload_router
from adapters.inbound.telegram.states.chat_link_upload_handler import router as chat_link_upload_router
from adapters.inbound.telegram.states.chat_target_id_upload_handler import router as chat_target_id_upload_router
from adapters.inbound.telegram.states.product_key_upload_handler import router as product_key_upload_router
from adapters.inbound.telegram.utils.messages import default_menu_commands, manager_menu_commands
from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort
from infra.telegram.bot_infra import TelegramBotInfra


class TelegramAdapter:
    def __init__(
        self,
        bot_infra: TelegramBotInfra,
        actions: AppActionsPort,
        logger: LoggerPort,
        manager_user_id: int,
    ):
        self.bot_infra = bot_infra
        self.actions = actions
        self.logger = logger
        self.manager_user_id = manager_user_id

        error_middleware = DomainErrorMiddleware(logger)
        antispam_middleware = AntiSpamMiddleware(logger, manager_user_id)
        ctx_middleware = DomainContextMiddleware(actions, logger)

        bot_infra.attach_router(messages_router)
        bot_infra.attach_router(banner_upload_router)
        bot_infra.attach_router(chat_link_upload_router)
        bot_infra.attach_router(chat_target_id_upload_router)
        bot_infra.attach_router(product_key_upload_router)
        bot_infra.attach_router(business_router)
        bot_infra.attach_router(reviews_router)
        bot_infra.attach_router(chat_members_router)

        for middleware in (error_middleware, antispam_middleware, ctx_middleware):
            bot_infra.attach_outer_at_message(middleware)
            bot_infra.attach_outer_at_business_message(middleware)
            bot_infra.attach_outer_at_edited_business_message(middleware)
        for middleware in (error_middleware, ctx_middleware):
            bot_infra.attach_outer_at_business_connection(middleware)
            bot_infra.attach_outer_at_callback_query(middleware)
            bot_infra.attach_outer_at_chat_member(middleware)
            bot_infra.attach_outer_at_chat_join_request(middleware)

        self.logger.info("Telegram bot loaded (aiogram)")

    async def configure_menu_commands(self) -> None:
        await self.bot_infra.bot.set_my_commands(
            default_menu_commands(),
            scope=BotCommandScopeAllPrivateChats(),
        )
        await self.bot_infra.bot.set_my_commands(
            manager_menu_commands(),
            scope=BotCommandScopeChat(chat_id=self.manager_user_id),
        )
        self.logger.info(f"Telegram menu commands manager={self.manager_user_id}")
