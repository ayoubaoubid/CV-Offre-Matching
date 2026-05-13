import re
import unicodedata

import pandas as pd


NOISE_PATTERNS = [
    r"^1\s*-\s*10\s+sur\s+\d+.*?Page\s+\d+(?:\s+\d+)*\s+sur",
    r"\bLancer\s+4K\b",
    r"\[\+\]",
]


def clean_text(value):
    if pd.isna(value) or value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_text(value):
    text = clean_text(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def looks_like_free_text(text, max_words=8, max_length=150):
    text = clean_text(text)
    if not text:
        return False
    return len(text) > max_length or len(text.split()) > max_words


def clean_rekrute_description(text):
    text = clean_text(text)
    if not text:
        return ""

    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\bPublication\s*:\s*du\s+.*$", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def clean_raw_text_for_nlp(text):
    text = normalize_text(text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def join_unique_parts(parts):
    values = []
    for part in parts:
        part = clean_text(part)
        if not part:
            continue
        values.append(part)
    return " ".join(dict.fromkeys(values))
