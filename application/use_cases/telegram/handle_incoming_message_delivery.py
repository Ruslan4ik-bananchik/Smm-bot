from __future__ import annotations

from application.ports.outbound.incoming_message_result_publisher import IncomingMessageResultPublisherPort
from application.use_cases.telegram.close_dialog import CloseDialog
from application.use_cases.telegram.process_incoming_message import ProcessIncomingMessage


class HandleIncomingMessageDelivery:
    def __init__(
        self,
        process_incoming_message: ProcessIncomingMessage,
        close_dialog: CloseDialog,
        publisher: IncomingMessageResultPublisherPort,
    ):
        self.process_incoming_message = process_incoming_message
        self.close_dialog = close_dialog
        self.publisher = publisher

    async def execute(
        self,
        *,
        user_id: int,
        dialog_id: int,
        text: str,
        history: list[str],
        response_flow: str,
        business_connection_id: str | None,
        applicant_username: str | None,
        source_message_link: str | None,
        reply_chat_id: int,
        reply_business_connection_id: str | None,
    ) -> None:
        result = await self.process_incoming_message.execute(
            user_id=user_id,
            dialog_id=dialog_id,
            text=text,
            history=history,
            response_flow=response_flow,
            business_connection_id=business_connection_id,
            applicant_username=applicant_username,
            source_message_link=source_message_link,
        )

        await self.publisher.publish_reply(
            result,
            chat_id=reply_chat_id,
            business_connection_id=reply_business_connection_id,
        )
        await self.publisher.publish_application_review(result.review_dispatch)

        technical_task_review_sent = await self.publisher.publish_technical_task_review(
            result.technical_task_review_dispatch
        )
        if technical_task_review_sent:
            await self.close_dialog.execute(dialog_id)

        await self.publisher.publish_technical_task_decline(result.technical_task_decline_dispatch)
        await self.publisher.publish_troll_report(result.troll_report_dispatch)
