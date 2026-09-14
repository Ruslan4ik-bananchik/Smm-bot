from domain.value_objects.application_form_code import ApplicationFormCode
from domain.value_objects.anti_troll_code import AntiTrollCode
from domain.value_objects.auto_close_code import AutoCloseCode
from domain.value_objects.technical_task_code import TechnicalTaskCode


class SanitizeMessage:
    @staticmethod
    def sanitize_answer_text(text: str) -> str:
        cleaned = AutoCloseCode.strip_all_codes(text)
        cleaned = ApplicationFormCode.strip_all_codes(cleaned)
        cleaned = TechnicalTaskCode.strip_all_codes(cleaned)
        cleaned = AntiTrollCode.strip_all_codes(cleaned)
        cleaned = cleaned.replace("**", "")
        return cleaned.strip()
