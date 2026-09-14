from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from adapters.inbound.telegram.states.product_key_upload import ChatLinkUploadState
from application.ports.inbound.app_actions_port import AppActionsPort

router = Router()


@router.message(ChatLinkUploadState.waiting_for_link, F.chat.type == "private")
async def handle_chat_link_upload(
    message: Message,
    state: FSMContext,
    actions: AppActionsPort,
) -> None:
    value = (message.text or message.caption or "").strip()
    await actions.set_chat_link.execute(
        actor_user_id=message.from_user.id if message.from_user else None,
        value=value,
    )
    await state.clear()
    await message.answer(f"Ссылка сохранена: {value}")
