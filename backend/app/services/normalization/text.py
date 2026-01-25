import re
import unicodedata
from typing import Optional

class TextNormalizer:
    @staticmethod
    def normalize(text: Optional[str]) -> Optional[str]:
        if not text:
            return text

        text = unicodedata.normalize("NFKD", text)
        text = text.lower()
        text = re.sub(r"[./,_\-]+", " ", text)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text
