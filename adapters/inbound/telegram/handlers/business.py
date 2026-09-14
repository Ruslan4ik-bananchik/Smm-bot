from __future__ import annotations

from aiogram import Router
from aiogram.types import BusinessConnection, Message

from adapters.inbound.telegram.utils.message_links import source_message_link
from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort

router = Router()


@router.business_message()
async def handle_business_message(
    message: Message,
    actions: AppActionsPort,
    logger: LoggerPort,
    user_id: int,
    dialog_id: int,
    history: list[str],
    response_flow: str,
    business_connection_id: str | None,
) -> None:
    text = (message.text or message.caption or "").strip()
    logger.info(f"Received business message from user {user_id}: {text}")
    await actions.handle_incoming_message_delivery.execute(
        user_id=user_id,
        dialog_id=dialog_id,
        text=text,
        history=history,
        response_flow=response_flow,
        business_connection_id=business_connection_id,
        applicant_username=message.from_user.username if message.from_user else None,
        source_message_link=source_message_link(message),
        reply_chat_id=message.chat.id,
        reply_business_connection_id=business_connection_id,
    )


@router.business_connection()
async def handle_business_connection(connection: BusinessConnection, logger: LoggerPort) -> None:
    logger.info(
        "Business connection update "
        f"id={connection.id} "
        f"user_id={connection.user.id} "
        f"enabled={connection.is_enabled} "
        f"can_reply={connection.can_reply}"
    )
