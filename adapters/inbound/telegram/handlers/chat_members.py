from __future__ import annotations

from aiogram import Router
from aiogram.types import ChatJoinRequest

from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort

router = Router()

@router.chat_join_request()
async def handle_chat_join_request(
    event: ChatJoinRequest,
    actions: AppActionsPort,
    logger: LoggerPort,
) -> None:
    applicant_user_id = event.from_user.id
    removed = await actions.complete_pending_chat_acceptance.execute(
        applicant_user_id=applicant_user_id,
        target_chat_id=event.chat.id,
    )
    if not removed:
        return

    try:
        await event.approve()
    except Exception as exc:
        logger.warning(
            "Failed to auto-approve chat join request "
            f"user_id={applicant_user_id} "
            f"chat_id={event.chat.id} "
            f"error={exc}"
        )
        return

    logger.info(
        "Pending chat acceptance completed and join request approved "
        f"user_id={applicant_user_id} "
        f"chat_id={event.chat.id}"
    )
