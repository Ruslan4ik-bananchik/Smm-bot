from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from adapters.inbound.telegram.states.product_key_upload import ChatTargetIdUploadState
from application.ports.inbound.app_actions_port import AppActionsPort

router = Router()


@router.message(ChatTargetIdUploadState.waiting_for_chat_id, F.chat.type == "private")
async def handle_chat_target_id_upload(
    message: Message,
    state: FSMContext,
    actions: AppActionsPort,
) -> None:
    value = (message.text or message.caption or "").strip()
    await actions.set_chat_target_id.execute(
        actor_user_id=message.from_user.id if message.from_user else None,
        value=value,
    )
    await state.clear()
    await message.answer(f"Chat ID сохранен: {value}")
