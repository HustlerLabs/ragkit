from __future__ import annotations

import re

from ragkit.core.base import Document


class Cleaner:
    def clean(self, docs: list[Document]) -> list[Document]:
        return [Document(content=self._clean_text(d.content), metadata=d.metadata) for d in docs]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = text.strip()
        return text
