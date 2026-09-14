from application.ports.inbound.app_actions_port import AppActionsPort
from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort
from application.ports.outbound.blocklist_repository import BlocklistRepositoryPort
from application.ports.outbound.claude_request import ClaudeRequestPort
from application.ports.outbound.conversation_repository import ConversationRepositoryPort
from application.ports.outbound.incoming_message_result_publisher import IncomingMessageResultPublisherPort
from application.ports.outbound.logger_port import LoggerPort
from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from application.use_cases.telegram import *
from infra.tz_clock import TZClock


class AppActions(AppActionsPort):
    def __init__(
        self,
        claude: ClaudeRequestPort,
        logger: LoggerPort,
        conversation_repo: ConversationRepositoryPort,
        blocklist_repo: BlocklistRepositoryPort,
        incoming_message_result_publisher: IncomingMessageResultPublisherPort,
        application_review_repo: ApplicationReviewRepositoryPort,
        technical_task_repo: TechnicalTaskRepositoryPort,
        telegram_asset_repo: TelegramAssetRepositoryPort,
        tz_clock: TZClock,
        manager_user_id: int,
        review_chat_id: int = 0,
        application_review_thread_id: int | None = None,
        technical_task_review_thread_id: int | None = None,
        technical_task_decline_thread_id: int | None = None,
        troll_report_thread_id: int | None = None,
    ):
        request_incoming_message_answer = RequestIncomingMessageAnswer(claude, logger)
        activate_technical_task = ActivateTechnicalTask(technical_task_repo)
        issue_technical_task_key = IssueTechnicalTaskKey(technical_task_repo, tz_clock)
        prepare_application_review_dispatch = PrepareApplicationReviewDispatch(
            repo=application_review_repo,
            manager_user_id=manager_user_id,
            review_chat_id=review_chat_id,
            application_review_thread_id=application_review_thread_id,
        )
        prepare_technical_task_review_dispatch = PrepareTechnicalTaskReviewDispatch(
            repo=technical_task_repo,
            manager_user_id=manager_user_id,
            review_chat_id=review_chat_id,
            technical_task_review_thread_id=technical_task_review_thread_id,
        )
        prepare_technical_task_decline_dispatch = PrepareTechnicalTaskDeclineDispatch(
            review_chat_id=review_chat_id,
            technical_task_decline_thread_id=technical_task_decline_thread_id,
        )
        prepare_troll_report_dispatch = PrepareTrollReportDispatch(
            review_chat_id=review_chat_id,
            troll_report_thread_id=troll_report_thread_id,
        )

        self.process_incoming_message = ProcessIncomingMessage(
            request_incoming_message_answer=request_incoming_message_answer,
            activate_technical_task=activate_technical_task,
            issue_technical_task_key=issue_technical_task_key,
            prepare_application_review_dispatch=prepare_application_review_dispatch,
            prepare_technical_task_review_dispatch=prepare_technical_task_review_dispatch,
            prepare_technical_task_decline_dispatch=prepare_technical_task_decline_dispatch,
            prepare_troll_report_dispatch=prepare_troll_report_dispatch,
            conversation_repo=conversation_repo,
            technical_task_repo=technical_task_repo,
        )
        self.handle_incoming_message_delivery = HandleIncomingMessageDelivery(
            process_incoming_message=self.process_incoming_message,
            close_dialog=CloseDialog(conversation_repo),
            publisher=incoming_message_result_publisher,
        )
        self.request_anwser = RequestAnwser(claude, logger)
        self.prepare_dialog_context = PrepareDialogContext(conversation_repo)
        self.store_dialog_message = StoreDialogMessage(conversation_repo)
        self.update_business_connection = UpdateBusinessConnection(conversation_repo)
        self.create_application_review = CreateApplicationReview(application_review_repo)
        self.resolve_application_review = ResolveApplicationReview(application_review_repo)
        self.prepare_application_review_dispatch = prepare_application_review_dispatch
        self.handle_application_review_callback = HandleApplicationReviewCallback(
            review_repo=application_review_repo,
            task_repo=technical_task_repo,
            asset_repo=telegram_asset_repo,
            claude=claude,
            manager_user_id=manager_user_id,
        )
        self.handle_technical_task_review_callback = HandleTechnicalTaskReviewCallback(
            repo=technical_task_repo,
            manager_user_id=manager_user_id,
        )
        self.activate_technical_task = activate_technical_task
        self.issue_technical_task_key = issue_technical_task_key
        self.upload_product_keys = UploadProductKeys(technical_task_repo, manager_user_id)
        self.upload_banner_file = UploadBannerFile(telegram_asset_repo, manager_user_id)
        self.get_banner_file = GetBannerFile(telegram_asset_repo)
        self.set_chat_link = SetChatLink(telegram_asset_repo, manager_user_id)
        self.get_chat_link = GetChatLink(telegram_asset_repo)
        self.set_chat_target_id = SetChatTargetId(telegram_asset_repo, manager_user_id)
        self.get_chat_target_id = GetChatTargetId(telegram_asset_repo)
        self.create_pending_chat_acceptance = CreatePendingChatAcceptance(technical_task_repo)
        self.complete_pending_chat_acceptance = CompletePendingChatAcceptance(technical_task_repo)
        self.close_dialog = CloseDialog(conversation_repo)
        self.access_check = AccessCheck(manager_user_id)
        self.add_to_blocklist = AddToBlocklist(blocklist_repo)
        self.remove_from_blocklist = RemoveFromBlocklist(blocklist_repo)
        self.is_blocked_in_blocklist = IsBlockedInBlocklist(blocklist_repo)
        self.validate_business_connection = ValidateBusinessConnection(manager_user_id, conversation_repo)
