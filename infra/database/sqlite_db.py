from __future__ import annotations

import asyncio
import sqlite3
import threading
from pathlib import Path
from typing import Callable, TypeVar

from infra.tz_clock import TZClock

T = TypeVar("T")


class SQLiteDatabase:
    def __init__(self, tz_clock: TZClock, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._lock = threading.RLock()
        self._configure()
        self._init_schema()

    def _configure(self) -> None:
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._conn.execute("PRAGMA busy_timeout=5000;")

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS dialog_state (
                    dialog_id INTEGER PRIMARY KEY,
                    human_takeover INTEGER NOT NULL DEFAULT 0,
                    auto_closed INTEGER NOT NULL DEFAULT 0,
                    troll_blocked INTEGER NOT NULL DEFAULT 0,
                    reject_cooldown_until TEXT,
                    application_retake_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS dialog_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dialog_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_dialog_messages_dialog_id_id ON dialog_messages(dialog_id, id DESC);

                CREATE TABLE IF NOT EXISTS business_connections (
                    connection_id TEXT PRIMARY KEY,
                    owner_user_id INTEGER NOT NULL,
                    is_enabled INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS dialog_guard (
                    dialog_id INTEGER PRIMARY KEY,
                    last_user_text TEXT NOT NULL,
                    last_user_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dialog_blocks (
                    dialog_id INTEGER PRIMARY KEY,
                    reason TEXT NOT NULL,
                    expires_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_dialog_blocks_expires_at ON dialog_blocks(expires_at);

                CREATE TABLE IF NOT EXISTS application_reviews (
                    token TEXT PRIMARY KEY,
                    manager_user_id INTEGER NOT NULL,
                    applicant_user_id INTEGER NOT NULL,
                    applicant_chat_id INTEGER NOT NULL,
                    applicant_username TEXT,
                    application_text TEXT NOT NULL,
                    video_format TEXT,
                    video_format_code TEXT,
                    business_connection_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    resolved_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technical_task_stage (
                    applicant_chat_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    task_type TEXT NOT NULL DEFAULT 'shorts',
                    business_connection_id TEXT,
                    current_step TEXT,
                    product_key TEXT,
                    key_count INTEGER NOT NULL DEFAULT 0,
                    max_key_count INTEGER NOT NULL DEFAULT 6,
                    task_sent_at TEXT,
                    first_key_time TEXT,
                    last_key_time TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    last_activity_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technical_task_reviews (
                    token TEXT PRIMARY KEY,
                    manager_user_id INTEGER NOT NULL,
                    applicant_user_id INTEGER NOT NULL,
                    applicant_chat_id INTEGER NOT NULL,
                    applicant_username TEXT,
                    submission_text TEXT NOT NULL,
                    business_connection_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    resolved_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technical_task_timeouts (
                    applicant_chat_id INTEGER PRIMARY KEY,
                    business_connection_id TEXT,
                    task_type TEXT NOT NULL,
                    timed_out_at TEXT NOT NULL,
                    notified_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technical_task_stage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    applicant_chat_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    notified_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(applicant_chat_id) REFERENCES technical_task_stage(applicant_chat_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_technical_task_stage_log_chat_id_created_at
                    ON technical_task_stage_log(applicant_chat_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS product_keys (
                    name TEXT PRIMARY KEY,
                    owner INTEGER,
                    issued_time TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_product_keys_owner ON product_keys(owner);

                CREATE TABLE IF NOT EXISTS telegram_assets (
                    name TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    file_name TEXT,
                    owner INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS telegram_text_assets (
                    name TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    owner INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS pending_chat_acceptances (
                    applicant_chat_id INTEGER PRIMARY KEY,
                    applicant_user_id INTEGER NOT NULL UNIQUE,
                    target_chat_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS troll_reports (
                    applicant_chat_id INTEGER PRIMARY KEY,
                    applicant_user_id INTEGER NOT NULL,
                    applicant_username TEXT,
                    troll_text TEXT NOT NULL,
                    source_message_link TEXT,
                    business_connection_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS blocked_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    async def in_transaction(self, fn: Callable[[sqlite3.Cursor], T]) -> T:
        return await asyncio.to_thread(self._in_transaction_sync, fn)

    def _in_transaction_sync(self, fn: Callable[[sqlite3.Cursor], T]) -> T:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                result = fn(cur)
                cur.execute("COMMIT")
                return result
            except Exception:
                cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()
