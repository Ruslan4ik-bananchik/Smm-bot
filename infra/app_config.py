from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from infra.logger import InfraLogger as LogConfigurator


def _read_str(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _read_int(name: str, default: int) -> int:
    raw = _read_str(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _read_float(name: str, default: float) -> float:
    raw = _read_str(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def ensure_runtime_dependencies(project_root: Path) -> None:
    try:
        for module_name in ("aiogram", "anthropic", "dotenv"):
            __import__(module_name)
    except ImportError as exc:
        requirements_path = project_root / "requirements.txt"
        if not requirements_path.exists():
            raise FileNotFoundError() from exc
        print(f"Missing dependency '{exc.name}'. Installing requirements.txt...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])


def read_required_env(logger: LogConfigurator, name: str, error_text: str) -> str | None:
    value = _read_str(name)
    if value:
        return value
    logger.error(error_text)
    return None


def read_manager_user_id(logger: LogConfigurator) -> int | None:
    raw_value = _read_str("MANAGER_USER_ID")
    try:
        manager_user_id = int(raw_value) if raw_value else None
    except ValueError:
        manager_user_id = None

    if manager_user_id:
        return manager_user_id

    logger.error("Не найден менеджер. Укажите MANAGER_USER_ID в .env")
    return None


@dataclass(frozen=True)
class ReviewInfraConfig:
    review_chat_id: int = -1003760771399
    application_review_thread_id: int = 4
    technical_task_review_thread_id: int = 2
    technical_task_decline_thread_id: int = 45
    troll_report_thread_id: int = 176
    technical_task_timeout_thread_id: int = 27
    technical_task_key_log_thread_id: int = 30
    technical_task_low_stock_thread_id: int = 87
    technical_task_key_log_interval_sec: float = 10.0

    @classmethod
    def from_env(cls) -> ReviewInfraConfig:
        return cls(
            review_chat_id=_read_int("REVIEW_CHAT_ID", cls.review_chat_id),
            application_review_thread_id=_read_int("APPLICATION_REVIEW_TOPIC_ID", cls.application_review_thread_id),
            technical_task_review_thread_id=_read_int(
                "TECHNICAL_TASK_REVIEW_TOPIC_ID",
                cls.technical_task_review_thread_id,
            ),
            technical_task_decline_thread_id=_read_int(
                "TECHNICAL_TASK_DECLINE_TOPIC_ID",
                cls.technical_task_decline_thread_id,
            ),
            troll_report_thread_id=_read_int("TROLL_REPORT_TOPIC_ID", cls.troll_report_thread_id),
            technical_task_timeout_thread_id=_read_int(
                "TECHNICAL_TASK_TIMEOUT_TOPIC_ID",
                cls.technical_task_timeout_thread_id,
            ),
            technical_task_key_log_thread_id=_read_int(
                "TECHNICAL_TASK_KEY_LOG_TOPIC_ID",
                cls.technical_task_key_log_thread_id,
            ),
            technical_task_low_stock_thread_id=_read_int(
                "TECHNICAL_TASK_LOW_STOCK_TOPIC_ID",
                cls.technical_task_low_stock_thread_id,
            ),
            technical_task_key_log_interval_sec=_read_float(
                "TECHNICAL_TASK_KEY_LOG_INTERVAL_SEC",
                cls.technical_task_key_log_interval_sec,
            ),
        )
