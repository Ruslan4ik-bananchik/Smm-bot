from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from adapters.inbound.telegram.storage.callback_prefixes import (
    APPLICATION_REVIEW_CALLBACK_PREFIX,
    BLOCK_USER_CALLBACK_PREFIX,
    TECHNICAL_TASK_REVIEW_CALLBACK_PREFIX,
)
from adapters.inbound.telegram.utils.review_callbacks import (
    build_application_review_callback_alert_text,
    build_application_review_callback_status_text,
    build_application_review_callback_user_text,
    build_technical_task_callback_alert_text,
    build_technical_task_callback_status_text,
    build_technical_task_callback_user_text,
    parse_callback_user_id,
    publish_manager_review_status,
)
from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort

router = Router()


@router.callback_query(F.data.startswith(f"{APPLICATION_REVIEW_CALLBACK_PREFIX}:"))
async def handle_review_callback(callback: CallbackQuery, actions: AppActionsPort, logger: LoggerPort) -> None:
    bot = callback.bot
    if bot is None:
        await callback.answer("Ошибка: бот недоступен", show_alert=True)
        return

    result = await actions.handle_application_review_callback.execute(
        actor_user_id=callback.from_user.id if callback.from_user else None,
        payload=callback.data,
    )

    try:
        user_text = build_application_review_callback_user_text(result)
        await bot.send_message(
            chat_id=result.applicant_chat_id,
            text=user_text,
            business_connection_id=result.business_connection_id,
            parse_mode=ParseMode.HTML,
        )
        if result.status == "approved":
            await actions.store_dialog_message.execute(
                dialog_id=result.applicant_chat_id,
                text=user_text,
                auto_close_eligible=False,
                force_auto_close=False,
            )
    except Exception as exc:
        logger.warning(
            "Business send failed "
            f"chat_id={result.applicant_chat_id} "
            f"connection_id={result.business_connection_id} "
            f"error={exc}"
        )
        await callback.answer("Не удалось отправить через business", show_alert=True)
        return

    if result.banner_file is not None:
        try:
            await bot.send_document(
                chat_id=result.applicant_chat_id,
                document=result.banner_file.file_id,
                caption=result.banner_file.file_name or "Баннер",
                business_connection_id=result.business_connection_id,
            )
        except Exception as exc:
            logger.warning(
                "Banner send via business failed "
                f"chat_id={result.applicant_chat_id} "
                f"connection_id={result.business_connection_id} "
                f"error={exc}"
            )
            try:
                await bot.send_document(
                    chat_id=result.applicant_chat_id,
                    document=result.banner_file.file_id,
                    caption=result.banner_file.file_name or "Баннер",
                )
            except Exception as fallback_exc:
                logger.warning(
                    "Banner send fallback failed "
                    f"chat_id={result.applicant_chat_id} "
                    f"error={fallback_exc}"
                )

    try:
        await publish_manager_review_status(callback, build_application_review_callback_status_text(result))
    except Exception:
        pass

    await callback.answer(build_application_review_callback_alert_text(result))


@router.callback_query(F.data.startswith(f"{TECHNICAL_TASK_REVIEW_CALLBACK_PREFIX}:"))
async def handle_technical_task_review_callback(
    callback: CallbackQuery, actions: AppActionsPort, logger: LoggerPort
) -> None:
    bot = callback.bot
    if bot is None:
        await callback.answer("Ошибка: бот недоступен", show_alert=True)
        return

    result = await actions.handle_technical_task_review_callback.execute(
        actor_user_id=callback.from_user.id if callback.from_user else None,
        payload=callback.data,
    )
    chat_link = await actions.get_chat_link.execute()
    target_chat_id = await actions.get_chat_target_id.execute()

    try:
        user_text = build_technical_task_callback_user_text(result, chat_link)
        await bot.send_message(
            chat_id=result.applicant_chat_id,
            text=user_text,
            business_connection_id=result.business_connection_id,
        )
        await actions.store_dialog_message.execute(
            dialog_id=result.applicant_chat_id,
            text=user_text,
            auto_close_eligible=False,
            force_auto_close=False,
        )
        if result.status == "approved" and chat_link and target_chat_id is not None:
            await actions.create_pending_chat_acceptance.execute(
                applicant_chat_id=result.applicant_chat_id,
                applicant_user_id=result.applicant_user_id,
                target_chat_id=target_chat_id,
            )
    except Exception as exc:
        logger.warning(
            "Technical task review send failed "
            f"chat_id={result.applicant_chat_id} "
            f"connection_id={result.business_connection_id} "
            f"error={exc}"
        )
        await callback.answer("Не удалось отправить решение по ТЗ через business", show_alert=True)
        return

    if result.status == "approved" and chat_link and target_chat_id is None:
        logger.warning(
            "Technical task approved without target chat id "
            f"applicant_chat_id={result.applicant_chat_id}"
        )

    try:
        await publish_manager_review_status(callback, build_technical_task_callback_status_text(result))
    except Exception:
        pass

    await callback.answer(build_technical_task_callback_alert_text(result))


@router.callback_query(F.data.startswith(f"{BLOCK_USER_CALLBACK_PREFIX}:"))
async def handle_block_user_callback(
    callback: CallbackQuery, actions: AppActionsPort, logger: LoggerPort
) -> None:
    actor_user_id = callback.from_user.id if callback.from_user else None
    if actor_user_id is None:
        await callback.answer("Ошибка: не удалось определить менеджера", show_alert=True)
        return

    await actions.access_check.execute(actor_user_id)

    try:
        target_user_id = parse_callback_user_id(callback.data, BLOCK_USER_CALLBACK_PREFIX)
    except ValueError:
        await callback.answer("Некорректная команда блокировки", show_alert=True)
        return

    await actions.add_to_blocklist.execute(
        target_user_id,
        reason=f"manual_block_from_report:{actor_user_id}",
    )
    logger.info(f"User added to permanent blocklist target={target_user_id} actor={actor_user_id}")

    try:
        await publish_manager_review_status(callback, f"Пользователь {target_user_id} заблокирован навсегда")
    except Exception:
        pass

    await callback.answer("Пользователь навсегда заблокирован")
