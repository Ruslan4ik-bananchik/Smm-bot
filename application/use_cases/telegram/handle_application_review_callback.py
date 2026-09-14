from __future__ import annotations

from application.dtos.application_review_callback_result import ApplicationReviewCallbackResultDTO
from application.dtos.telegram_asset_file_view import TelegramAssetFileViewDTO
from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort
from application.ports.outbound.claude_request import ClaudeRequestPort
from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.exceptions.errors import (
    ManagerNotConfiguredError,
    ReviewAccessDeniedError,
    ReviewAlreadyProcessedError,
    ReviewBusinessConnectionMissingError,
    ReviewNotFoundError,
    ReviewPayloadInvalidError,
)
from domain.services.technical_task_profile import TechnicalTaskProfileResolver


class HandleApplicationReviewCallback:
    CALLBACK_PREFIX = "review"

    def __init__(
        self,
        review_repo: ApplicationReviewRepositoryPort,
        task_repo: TechnicalTaskRepositoryPort,
        asset_repo: TelegramAssetRepositoryPort,
        claude: ClaudeRequestPort,
        manager_user_id: int | None,
    ):
        self.review_repo = review_repo
        self.task_repo = task_repo
        self.asset_repo = asset_repo
        self.claude = claude
        self.manager_user_id = manager_user_id

    async def execute(self, *, actor_user_id: int | None, payload: str | None) -> ApplicationReviewCallbackResultDTO:
        if self.manager_user_id is None:
            raise ManagerNotConfiguredError()
        if actor_user_id != self.manager_user_id:
            raise ReviewAccessDeniedError()

        raw_payload = payload or ""
        parts = raw_payload.split(":", 2)
        if len(parts) != 3 or parts[0] != self.CALLBACK_PREFIX:
            raise ReviewPayloadInvalidError()

        _, action, token = parts
        if action not in {"approve", "reject"}:
            raise ReviewPayloadInvalidError()

        resolution = await self.review_repo.resolve_application_review(token=token, approved=(action == "approve"))
        if resolution is None:
            raise ReviewNotFoundError()
        if not resolution.was_updated:
            raise ReviewAlreadyProcessedError()
        if not resolution.business_connection_id:
            raise ReviewBusinessConnectionMissingError()

        banner_file: TelegramAssetFileViewDTO | None = None
        technical_task_text: str | None = None
        if resolution.status == "approved":
            profile = TechnicalTaskProfileResolver.resolve(resolution.video_format_code)
            await self.task_repo.start_technical_task_stage_with_connection(
                applicant_chat_id=resolution.applicant_chat_id,
                task_type=profile.task_type,
                max_key_count=profile.max_key_count,
                business_connection_id=resolution.business_connection_id,
            )
            technical_task_text = await self.claude.generate_technical_task_offer(
                resolution.video_format_code,
                profile.task_text,
            )
            if profile.task_type == "shorts":
                asset = await self.asset_repo.get_asset_file(TechnicalTaskProfileResolver.SHORTS_BANNER_ASSET)
                if asset is not None:
                    file_id, file_name = asset
                    banner_file = TelegramAssetFileViewDTO(file_id=file_id, file_name=file_name)

        return ApplicationReviewCallbackResultDTO(
            applicant_chat_id=resolution.applicant_chat_id,
            business_connection_id=resolution.business_connection_id,
            status=resolution.status,
            video_format_code=resolution.video_format_code,
            technical_task_text=technical_task_text,
            banner_file=banner_file,
            should_auto_close_dialog=resolution.status != "approved",
        )
