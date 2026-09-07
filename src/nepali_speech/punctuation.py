"""Sentence punctuation accepted by the VITS cleaner."""
import re
import unicodedata


def normalize_punctuation(text):
    text = unicodedata.normalize("NFC", text).replace("।", ".").replace("॥", ".")
    text = re.sub(r"[!?]+", ".", text)
    return re.sub(r"\s+", " ", text).strip()
