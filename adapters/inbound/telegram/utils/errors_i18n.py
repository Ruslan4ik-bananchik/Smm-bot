from typing import Dict

ERROR_MESSAGES: Dict[str, str] = {
    "message_is_empty": "Сообщение не может быть пустым.",
    "message_looks_corrupted": "Сообщение выглядит поврежденным или нечитаемым. Пришли его обычным текстом одним сообщением.",
    "only_text_messages_allowed": "Разрешены только текстовые сообщения.",
    "unhandled_exception": "Произошла непредвиденная ошибка.",
    "message_is_useless": "Сообщение слишком короткое или не содержит полезной информации.",
    "manager_not_configured": "Менеджер не настроен.",
    "review_payload_invalid": "Некорректная кнопка заявки.",
    "review_access_denied": "Недостаточно прав для обработки заявки.",
    "review_not_found": "Заявка не найдена.",
    "review_already_processed": "Заявка уже обработана.",
    "review_business_connection_missing": "У пользователя нет business-подключения для отправки.",
    "technical_task_key_not_assigned": "Ключ пока не привязан к этому этапу. Менеджер добавит его отдельно.",
    "technical_task_key_reissue_too_early": "Ключ уже выдавался. Повторно его можно запросить только через 24 часа после последней выдачи.",
    "technical_task_key_limit_reached": "Лимит выдачи ключа исчерпан.",
    "product_key_pool_empty": "Свободных ключей сейчас нет.",
    "product_key_upload_access_denied": "Загружать ключи может только менеджер.",
    "product_key_file_expected": "Нужен `.txt` файл с ключами, по одному ключу на строку.",
    "product_key_file_invalid": "Не удалось распознать ключи из файла.",
    "banner_upload_access_denied": "Загружать баннер может только менеджер.",
    "banner_file_expected": "Нужно отправить файл баннера документом.",
    "banner_not_uploaded": "Баннер еще не загружен менеджером.",
    "not_manager": "Это действие доступно только менеджеру.",
    "chat_target_id_invalid": "Нужен корректный chat_id, например -1001234567890.",
    "technical_task_submission_invalid_link_count": "Нужно прислать все ссылки на готовые видео одним сообщением и в полном количестве для этого ТЗ.",
    "technical_task_submission_invalid_platform": "Ссылки не соответствуют платформам этого ТЗ. Отправь работы только на подходящих площадках.",
    "application_retake_limit_reached": "Анкету можно перезаполнить только один раз. Если нужно менять ее снова, это уже через менеджера.",
    "application_retake_after_technical_task_start": "После согласия на тестовое задание анкету менять уже нельзя. Дальше только выполнение ТЗ или отказ от него.",
}


def get_error_message(code: str) -> str:
    return ERROR_MESSAGES.get(code, "Неизвестная ошибка")
