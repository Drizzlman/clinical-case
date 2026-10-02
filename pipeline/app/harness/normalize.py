"""Text normalization for stable field comparison during evaluation."""

from __future__ import annotations

import re
import unicodedata

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Fold case, strip punctuation, and collapse whitespace."""

    folded = unicodedata.normalize("NFKC", text).casefold()
    without_punctuation = _PUNCTUATION.sub(" ", folded)
    return _WHITESPACE.sub(" ", without_punctuation).strip()
