from __future__ import annotations

from application.dtos.anwser import AnwserDTO
from application.dtos.application_form import ApplicationFormDTO
from application.ports.outbound.claude_request import ClaudeRequestPort
from application.ports.outbound.logger_port import LoggerPort
from domain.entities.message import Message
from domain.exceptions.errors import UnhandledException
from domain.services.base_msg_check import CheckMessage
from domain.services.message_noise_policy import MessageNoisePolicy
from domain.services.sanitize_answer_text import SanitizeMessage
from domain.value_objects.anti_troll_code import AntiTrollCode
from domain.value_objects.application_form_code import ApplicationFormCode
from domain.value_objects.auto_close_code import AutoCloseCode
from domain.value_objects.technical_task_code import TechnicalTaskCode


class RequestIncomingMessageAnswer:
    def __init__(self, claude: ClaudeRequestPort, logger: LoggerPort):
        self.claude = claude
        self.logger = logger

    async def execute(self, *, user_id: int, text: str, history: list[str], flow: str) -> AnwserDTO:
        CheckMessage.check(user_id, text)

        if MessageNoisePolicy.looks_like_mass_noise(text):
            self.logger.info(f"Blocked noisy message before LLM for user {user_id}")
            return AnwserDTO(
                text="",
                should_block_as_troll=True,
            )

        self.logger.info(f"Requesting answer for user {user_id} with text: {text}")
        anwser = await self.claude.request_anwser(
            Message(sender_id=user_id, text=text, history=history, flow=flow)
        )
        if not anwser or not anwser.text:
            self.logger.error(f"Failed to get a valid answer for user {user_id} with text: {text}")
            raise UnhandledException()

        should_auto_close = AutoCloseCode.has_close_code(anwser.text)
        parsed_form = ApplicationFormCode.parse(anwser.text) if should_auto_close else None
        application_form = (
            ApplicationFormDTO(
                montage=parsed_form["montage"],
                experience=parsed_form["experience"],
                game=parsed_form["game"],
                channel=parsed_form["channel"],
                video_format=parsed_form["format"],
                video_format_code=parsed_form["format_code"],
            )
            if parsed_form is not None
            else None
        )

        cleaned_answer = AnwserDTO(
            text=SanitizeMessage.sanitize_answer_text(anwser.text),
            should_auto_close=should_auto_close,
            application_form=application_form,
            should_issue_product_key=TechnicalTaskCode.should_issue_key(anwser.text),
            should_activate_technical_task=TechnicalTaskCode.should_activate_task(anwser.text),
            should_complete_technical_task=TechnicalTaskCode.should_complete_task(anwser.text),
            should_decline_technical_task=TechnicalTaskCode.should_decline_task(anwser.text),
            should_block_as_troll=AntiTrollCode.should_block(anwser.text),
        )
        self.logger.info(f"Received answer for user {user_id}: {cleaned_answer}")
        return cleaned_answer
