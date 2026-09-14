from __future__ import annotations

import unicodedata

from domain.exceptions.errors import MessageIsEmptyError, MessageLooksCorruptedError

class CheckMessage:
    MIN_CORRUPTED_LENGTH = 80
    MAX_COMBINING_RATIO = 0.35
    MIN_VISIBLE_ALNUM_RATIO = 0.05

    @staticmethod
    def check(sender_id: int, text: str) -> bool:
        stripped_text = text.strip().lower()
        if not stripped_text:
            raise MessageIsEmptyError()

        if CheckMessage._looks_corrupted(stripped_text):
            raise MessageLooksCorruptedError()
        
        return True

    @classmethod
    def _looks_corrupted(cls, text: str) -> bool:
        if len(text) < cls.MIN_CORRUPTED_LENGTH:
            return False

        combining_count = sum(1 for char in text if unicodedata.combining(char))
        if combining_count == 0:
            return False

        non_space_chars = [char for char in text if not char.isspace()]
        if not non_space_chars:
            return False

        visible_alnum_count = sum(
            1
            for char in non_space_chars
            if not unicodedata.combining(char) and char.isalnum()
        )
        combining_ratio = combining_count / len(non_space_chars)
        visible_alnum_ratio = visible_alnum_count / len(non_space_chars)

        return (
            combining_ratio >= cls.MAX_COMBINING_RATIO
            and visible_alnum_ratio <= cls.MIN_VISIBLE_ALNUM_RATIO
        )
