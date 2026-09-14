from __future__ import annotations

from domain.entities.product_key import ProductKey
from domain.exceptions.errors import ProductKeyFileInvalidError


class ProductKeyParser:
    @staticmethod
    def parse(raw_text: str) -> list[ProductKey]:
        seen: set[str] = set()
        result: list[ProductKey] = []
        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line in seen:
                continue
            seen.add(line)
            result.append(ProductKey(line))

        if not result:
            raise ProductKeyFileInvalidError()
        return result
