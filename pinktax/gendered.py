"""Gendered marketing words, stripped before anything is sent to Claude."""

import re

_FOR_PHRASE = r"\bfor\s+(?:her|him|women|men|ladies|girls|boys|guys)\b"
_WORDS = (
    r"\b(?:women|woman|womens|men|man|mens|ladies|lady|girls?|boys?|guys?|gents?"
    r"|female|male|feminine|masculine|her|hers|him|his|pink)(?:['’]s)?\b"
)
GENDERED = re.compile(f"{_FOR_PHRASE}|{_WORDS}", re.IGNORECASE)


def contains_gendered(text: str) -> bool:
    return bool(GENDERED.search(text))


def strip_gendered(text: str) -> str:
    """Remove gendered words, then tidy leftover whitespace and punctuation."""
    text = re.sub(r"\s+", " ", GENDERED.sub(" ", text))
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,;:])(?:\s*[,;:])+", r"\1", text)
    return text.strip(" ,;:-")
