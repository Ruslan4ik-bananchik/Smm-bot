from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProductKeyUploadState(StatesGroup):
    waiting_for_txt = State()


class BannerUploadState(StatesGroup):
    waiting_for_file = State()


class ChatLinkUploadState(StatesGroup):
    waiting_for_link = State()


class ChatTargetIdUploadState(StatesGroup):
    waiting_for_chat_id = State()
