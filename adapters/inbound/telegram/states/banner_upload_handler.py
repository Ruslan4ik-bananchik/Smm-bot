from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from adapters.inbound.telegram.states.product_key_upload import BannerUploadState
from adapters.inbound.telegram.utils.messages import ensure_banner_document
from application.ports.inbound.app_actions_port import AppActionsPort

router = Router()


@router.message(BannerUploadState.waiting_for_file, F.chat.type == "private")
async def handle_banner_upload(
    message: Message,
    state: FSMContext,
    actions: AppActionsPort,
) -> None:
    document = ensure_banner_document(message.document)
    await actions.upload_banner_file.execute(
        actor_user_id=message.from_user.id if message.from_user else None,
        file_id=document.file_id,
        file_name=document.file_name,
    )
    await state.clear()
    await message.answer("Баннер сохранен. Теперь его можно выдавать по команде /banner.")
