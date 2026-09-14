from __future__ import annotations

class ApplicationFormCode:
    PREFIX = "SYSTEM_FORM:"
    SHORTS_CODE = "shorts"
    LONGFORM_CODE = "longform"

    @classmethod
    def parse(cls, text: str) -> dict[str, str] | None:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith(cls.PREFIX):
                continue

            payload = line[len(cls.PREFIX):].strip()
            if not payload:
                return None

            normalized = payload
            if normalized.startswith("SMM_FORM_V1|"):
                normalized = normalized.split("|", 1)[1]

            parts = [part.strip() for part in normalized.split("||") if part.strip()]
            values: dict[str, str] = {}
            for part in parts:
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                values[key.strip().lower()] = value.strip()

            required = ("montage", "experience", "game", "channel", "format", "format_code")
            if not all(values.get(key) for key in required):
                return None
            format_code = values["format_code"].lower()
            if format_code not in {cls.SHORTS_CODE, cls.LONGFORM_CODE}:
                return None

            return {
                "montage": values["montage"],
                "experience": values["experience"],
                "game": values["game"],
                "channel": values["channel"],
                "format": values["format"],
                "format_code": format_code,
            }
        return None

    @classmethod
    def strip_all_codes(cls, text: str) -> str:
        lines = [line for line in text.splitlines() if not line.strip().startswith(cls.PREFIX)]
        return "\n".join(lines)
