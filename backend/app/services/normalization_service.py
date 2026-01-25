# app/normalization/universal.py
import re
import unicodedata
from typing import Optional

class TextNormalizer:

    @staticmethod
    def normalize(text: Optional[str]) -> Optional[str]:
        if not text:
            return text

        # Unicode normalization
        text = unicodedata.normalize("NFKD", text)

        # Lowercase
        text = text.lower()




        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text
