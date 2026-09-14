class DomainError(Exception):
    code: str

    def __str__(self) -> str:
        if self.args:
            return str(self.args[0])
        return self.code


class MessageIsEmptyError(DomainError):
    code = "message_is_empty"


class MessageLooksCorruptedError(DomainError):
    code = "message_looks_corrupted"


class OnlyTextMessagesAllowedError(DomainError):
    code = "only_text_messages_allowed"


class UnhandledException(DomainError):
    code = "unhandled_exception"


class MessageIsUselessError(DomainError):
    code = "message_is_useless"


class ManagerNotConfiguredError(DomainError):
    code = "manager_not_configured"


class ReviewPayloadInvalidError(DomainError):
    code = "review_payload_invalid"


class ReviewAccessDeniedError(DomainError):
    code = "review_access_denied"


class ReviewNotFoundError(DomainError):
    code = "review_not_found"


class ReviewAlreadyProcessedError(DomainError):
    code = "review_already_processed"


class ReviewBusinessConnectionMissingError(DomainError):
    code = "review_business_connection_missing"


class TechnicalTaskKeyNotAssignedError(DomainError):
    code = "technical_task_key_not_assigned"


class TechnicalTaskKeyReissueTooEarlyError(DomainError):
    code = "technical_task_key_reissue_too_early"


class TechnicalTaskKeyLimitReachedError(DomainError):
    code = "technical_task_key_limit_reached"


class ProductKeyPoolEmptyError(DomainError):
    code = "product_key_pool_empty"


class ProductKeyUploadAccessDeniedError(DomainError):
    code = "product_key_upload_access_denied"


class ProductKeyFileExpectedError(DomainError):
    code = "product_key_file_expected"


class ProductKeyFileInvalidError(DomainError):
    code = "product_key_file_invalid"


class BannerUploadAccessDeniedError(DomainError):
    code = "banner_upload_access_denied"


class BannerFileExpectedError(DomainError):
    code = "banner_file_expected"


class BannerNotUploadedError(DomainError):
    code = "banner_not_uploaded"


class NotManagerError(DomainError):
    code = "not_manager"


class TechnicalTaskSubmissionInvalidLinkCountError(DomainError):
    code = "technical_task_submission_invalid_link_count"


class TechnicalTaskSubmissionInvalidPlatformError(DomainError):
    code = "technical_task_submission_invalid_platform"


class ChatTargetIdInvalidError(DomainError):
    code = "chat_target_id_invalid"


class ApplicationRetakeLimitReachedError(DomainError):
    code = "application_retake_limit_reached"


class ApplicationRetakeAfterTechnicalTaskStartError(DomainError):
    code = "application_retake_after_technical_task_start"
