from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from adapters.inbound.telegram.states.product_key_upload import ProductKeyUploadState
from adapters.inbound.telegram.utils.messages import ensure_txt_document, read_txt_document
from application.ports.inbound.app_actions_port import AppActionsPort

router = Router()


@router.message(ProductKeyUploadState.waiting_for_txt, F.chat.type == "private")
async def handle_key_upload(
    message: Message,
    state: FSMContext,
    actions: AppActionsPort,
) -> None:
    document = ensure_txt_document(message.document)
    raw_text = await read_txt_document(message.bot, document)
    inserted = await actions.upload_product_keys.execute(
        actor_user_id=message.from_user.id if message.from_user else None,
        raw_text=raw_text,
    )
    await state.clear()
    await message.answer(f"Импорт завершен. Добавлено ключей: {inserted}")
