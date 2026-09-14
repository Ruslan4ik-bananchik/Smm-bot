from __future__ import annotations

from dataclasses import dataclass

from application.dtos.telegram_asset_file_view import TelegramAssetFileViewDTO


@dataclass(frozen=True)
class ApplicationReviewCallbackResultDTO:
    applicant_chat_id: int
    business_connection_id: str
    status: str
    video_format_code: str | None = None
    technical_task_text: str | None = None
    banner_file: TelegramAssetFileViewDTO | None = None
    should_auto_close_dialog: bool = False
