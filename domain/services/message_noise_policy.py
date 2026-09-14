from __future__ import annotations

import re


class MessageNoisePolicy:
    MIN_LONG_TEXT_LENGTH = 120
    MAX_UNIQUE_CHAR_RATIO = 0.12
    MAX_DOMINANT_CHAR_RATIO = 0.72
    MIN_REPEATED_CHAR_RUN = 80
    MIN_REPEATED_TOKEN_COUNT = 12
    TOKEN_PATTERN = re.compile(r"\S+")

    @classmethod
    def looks_like_mass_noise(cls, text: str) -> bool:
        normalized = (text or "").strip().lower()
        if len(normalized) < cls.MIN_LONG_TEXT_LENGTH:
            return False

        compact = "".join(char for char in normalized if not char.isspace())
        if not compact:
            return False

        if cls._has_long_repeated_char_run(compact):
            return True
        if cls._has_extremely_low_char_diversity(compact):
            return True
        if cls._has_repeated_same_token(normalized):
            return True
        return False

    @classmethod
    def _has_extremely_low_char_diversity(cls, compact: str) -> bool:
        unique_chars = set(compact)
        unique_ratio = len(unique_chars) / len(compact)
        dominant_char_ratio = max(compact.count(char) for char in unique_chars) / len(compact)
        return (
            unique_ratio <= cls.MAX_UNIQUE_CHAR_RATIO
            and dominant_char_ratio >= cls.MAX_DOMINANT_CHAR_RATIO
        )

    @classmethod
    def _has_long_repeated_char_run(cls, compact: str) -> bool:
        max_run = 1
        current_run = 1
        previous_char = compact[0]

        for char in compact[1:]:
            if char == previous_char:
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                previous_char = char
                current_run = 1

        return max_run >= cls.MIN_REPEATED_CHAR_RUN

    @classmethod
    def _has_repeated_same_token(cls, text: str) -> bool:
        tokens = cls.TOKEN_PATTERN.findall(text)
        if len(tokens) < cls.MIN_REPEATED_TOKEN_COUNT:
            return False

        first_token = tokens[0]
        return all(token == first_token for token in tokens)
