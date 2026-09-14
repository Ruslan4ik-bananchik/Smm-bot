import sys
from pathlib import Path

sys.dont_write_bytecode = True

import asyncio
import os
import signal

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from infra.app_config import (
    ReviewInfraConfig,
    ensure_runtime_dependencies,
    read_manager_user_id,
    read_required_env,
)

ensure_runtime_dependencies(PROJECT_ROOT)

from adapters.inbound.telegram.app import TelegramAdapter
from adapters.outbound.claude_haiku_request import ClaudeHaikuRequest
from adapters.outbound.repositories.application_review_repository import SQLiteApplicationReviewRepository
from adapters.outbound.repositories.blocklist_repository import SQLiteBlocklistRepository
from adapters.outbound.repositories.conversation_repository import SQLiteConversationRepository
from adapters.outbound.repositories.telegram_asset_repository import SQLiteTelegramAssetRepository
from adapters.outbound.repositories.technical_task_repository import SQLiteTechnicalTaskRepository
from adapters.outbound.telegram_incoming_message_result_publisher import TelegramIncomingMessageResultPublisher
from adapters.outbound.technical_task_key_log_dispatcher import TechnicalTaskKeyLogDispatcher
from adapters.outbound.technical_task_timeout_dispatcher import TechnicalTaskTimeoutDispatcher
from application.app_actions import AppActions
from dotenv import load_dotenv
from infra.database import SQLiteDatabase
from infra.logger import InfraLogger as LogConfigurator
from infra.scheduler import InfraScheduler
from infra.telegram.bot_infra import TelegramBotInfra
from infra.tz_clock import TZClock

load_dotenv()


async def wait_shutdown() -> None:
    stop_event = asyncio.Event()

    def signal_handler() -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

    await stop_event.wait()


async def shutdown(bot_infra: TelegramBotInfra, scheduler: InfraScheduler, logger: LogConfigurator) -> None:
    await scheduler.stop()
    await bot_infra.stop_polling()
    logger.info("Successful shutdown")


async def main() -> None:
    tz_clock = TZClock(os.getenv("TIMEZONE", "UTC"))

    logger = LogConfigurator(tz_clock=tz_clock, name="app", log_dir=str(PROJECT_ROOT / "logs"))
    logger.info("Program start...")

    claude_token = read_required_env(logger, "CLAUDE_TOKEN", "Токен Claude не найден. Укажи CLAUDE_TOKEN в .env")
    if not claude_token:
        return

    bot_token = read_required_env(logger, "BOT_TOKEN", "Токен бота не найден. Укажи BOT_TOKEN в .env")
    if not bot_token:
        return

    manager_user_id = read_manager_user_id(logger)
    if manager_user_id is None:
        return

    review_config = ReviewInfraConfig.from_env()

    bot_infra = TelegramBotInfra(tg_bot_token=bot_token)
    database = SQLiteDatabase(tz_clock, db_path=str(PROJECT_ROOT / "data" / "dialog_state.db"))
    conversation_repo = SQLiteConversationRepository(database)
    blocklist_repo = SQLiteBlocklistRepository(database)
    application_review_repo = SQLiteApplicationReviewRepository(database)
    technical_task_repo = SQLiteTechnicalTaskRepository(database)
    telegram_asset_repo = SQLiteTelegramAssetRepository(database)

    app_actions = AppActions(
        claude=ClaudeHaikuRequest(token=claude_token),
        logger=logger,
        conversation_repo=conversation_repo,
        blocklist_repo=blocklist_repo,
        incoming_message_result_publisher=TelegramIncomingMessageResultPublisher(
            bot=bot_infra.bot,
            logger=logger,
        ),
        application_review_repo=application_review_repo,
        technical_task_repo=technical_task_repo,
        telegram_asset_repo=telegram_asset_repo,
        tz_clock=tz_clock,
        manager_user_id=manager_user_id,
        review_chat_id=review_config.review_chat_id,
        application_review_thread_id=review_config.application_review_thread_id,
        technical_task_review_thread_id=review_config.technical_task_review_thread_id,
        technical_task_decline_thread_id=review_config.technical_task_decline_thread_id,
        troll_report_thread_id=review_config.troll_report_thread_id,
    )

    telegram_adapter = TelegramAdapter(
        bot_infra,
        app_actions,
        logger,
        manager_user_id=manager_user_id,
    )

    timeout_dispatcher = TechnicalTaskTimeoutDispatcher(
        bot=bot_infra.bot,
        repo=technical_task_repo,
        logger=logger,
        review_chat_id=review_config.review_chat_id,
        message_thread_id=review_config.technical_task_timeout_thread_id,
    )
    technical_task_key_log_dispatcher = TechnicalTaskKeyLogDispatcher(
        bot=bot_infra.bot,
        repo=technical_task_repo,
        logger=logger,
        review_chat_id=review_config.review_chat_id,
        message_thread_id=review_config.technical_task_key_log_thread_id,
        low_stock_thread_id=review_config.technical_task_low_stock_thread_id,
    )

    scheduler = InfraScheduler(logger=logger)
    scheduler.register_interval(
        name="technical_task_timeout_dispatch",
        interval_sec=60,
        handler=timeout_dispatcher.run_once,
    )
    scheduler.register_interval(
        name="technical_task_key_log_dispatch",
        interval_sec=review_config.technical_task_key_log_interval_sec,
        handler=technical_task_key_log_dispatcher.run_once,
    )

    await telegram_adapter.configure_menu_commands()
    await bot_infra.start_polling()
    await scheduler.start()

    logger.info("Program started")
    await wait_shutdown()
    await shutdown(bot_infra, scheduler, logger)


if __name__ == "__main__":
    asyncio.run(main())
