from abc import ABC
from application.use_cases.telegram import *


class AppActionsPort(ABC):
    handle_incoming_message_delivery: HandleIncomingMessageDelivery
    process_incoming_message: ProcessIncomingMessage
    request_anwser: RequestAnwser
    prepare_dialog_context: PrepareDialogContext
    store_dialog_message: StoreDialogMessage
    update_business_connection: UpdateBusinessConnection
    create_application_review: CreateApplicationReview
    resolve_application_review: ResolveApplicationReview
    prepare_application_review_dispatch: PrepareApplicationReviewDispatch
    handle_application_review_callback: HandleApplicationReviewCallback
    handle_technical_task_review_callback: HandleTechnicalTaskReviewCallback
    issue_technical_task_key: IssueTechnicalTaskKey
    activate_technical_task: ActivateTechnicalTask
    upload_product_keys: UploadProductKeys
    upload_banner_file: UploadBannerFile
    get_banner_file: GetBannerFile
    set_chat_link: SetChatLink
    get_chat_link: GetChatLink
    set_chat_target_id: SetChatTargetId
    get_chat_target_id: GetChatTargetId
    create_pending_chat_acceptance: CreatePendingChatAcceptance
    complete_pending_chat_acceptance: CompletePendingChatAcceptance
    close_dialog: CloseDialog
    access_check: AccessCheck
    add_to_blocklist: AddToBlocklist
    remove_from_blocklist: RemoveFromBlocklist
    is_blocked_in_blocklist: IsBlockedInBlocklist
    validate_business_connection: ValidateBusinessConnection
