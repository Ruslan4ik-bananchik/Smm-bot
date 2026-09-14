from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from adapters.inbound.telegram.filters.private_bot_message import PrivateBotMessageAccessFilter
from adapters.inbound.telegram.states.product_key_upload import (
    BannerUploadState,
    ChatLinkUploadState,
    ChatTargetIdUploadState,
    ProductKeyUploadState,
)
from adapters.inbound.telegram.utils.message_links import source_message_link
from adapters.inbound.telegram.utils.messages import help_commands
from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.logger_port import LoggerPort

router = Router()
router.message.filter(PrivateBotMessageAccessFilter())


@router.message(Command("upload_keys"))
async def start_key_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(ProductKeyUploadState.waiting_for_txt)
    await message.answer("Пришли `.txt` файл с ключами, по одному ключу на строку.")


@router.message(Command("upload_banner"))
async def start_banner_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(BannerUploadState.waiting_for_file)
    await message.answer("Пришли файл баннера документом. Я сохраню сам Telegram-файл, без ссылки.")


@router.message(Command("banner"))
async def send_banner(message: Message, actions: AppActionsPort) -> None:
    banner = await actions.get_banner_file.execute()
    await message.answer_document(
        document=banner.file_id,
        caption=banner.file_name or "Баннер",
    )


@router.message(Command("set_link"))
async def start_chat_link_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(ChatLinkUploadState.waiting_for_link)
    await message.answer("Пришли ссылку на чат одним сообщением.")


@router.message(Command("set_link_chat_id"))
async def start_chat_target_id_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(ChatTargetIdUploadState.waiting_for_chat_id)
    await message.answer("Пришли chat_id нужного чата одним сообщением. Пример: -1001234567890")


@router.message(Command("help"))
async def send_all_commands(message: Message) -> None:
    await message.answer(help_commands())


@router.message(Command("ban"))
async def ban_user(message: Message, actions: AppActionsPort) -> None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Используй: /ban {user_id}")
        return

    try:
        user_id = int(parts[1].strip())
    except ValueError:
        await message.answer("Нужен числовой user_id. Пример: /ban 123456789")
        return

    actor_user_id = message.from_user.id if message.from_user else "unknown"
    await actions.add_to_blocklist.execute(user_id, reason=f"manual_ban_by_manager:{actor_user_id}")
    await message.answer(f"Пользователь {user_id} добавлен в блоклист навсегда.")


@router.message(Command("unban"))
async def unban_user(message: Message, actions: AppActionsPort) -> None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Используй: /unban {user_id}")
        return

    try:
        user_id = int(parts[1].strip())
    except ValueError:
        await message.answer("Нужен числовой user_id. Пример: /unban 123456789")
        return

    removed = await actions.remove_from_blocklist.execute(user_id)
    if removed:
        await message.answer(f"Пользователь {user_id} удалён из блоклиста.")
        return

    await message.answer(f"Пользователь {user_id} не найден в блоклисте.")


@router.message(StateFilter(None))
async def handle_private_message(
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
    logger.info(f"Received message from user {user_id}: {text}")
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
