"""Ordered transformations with an auditable, JSON-friendly change list."""
from dataclasses import dataclass
import re
from .normalize import normalize_values
from .punctuation import normalize_punctuation
from .pronunciation import acronym, english_pronunciation
from .transliterate import transliterate_word


@dataclass
class PreparedText:
    text: str
    changes: list[dict[str, str]]


def prepare_text(text: str, overrides: dict[str, str] | None = None, *, romanized: str = "disabled") -> PreparedText:
    """Prepare speech text; each change records kind, before, and after.

    Overrides are case-insensitive whole words/phrases; longest match wins.
    Set romanized="enabled" to transliterate Latin words with optional IndicXlit.
    The default disabled mode uses English pronunciation and never loads IndicXlit.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if romanized not in {"enabled", "disabled"}:
        raise ValueError("romanized must be enabled or disabled")
    changes = []
    def replace(pattern, fn, value, kind):
        def apply(match):
            after = fn(match)
            if after != match[0]:
                changes.append({"kind": kind, "before": match[0], "after": after})
            return after
        return pattern.sub(apply, value)

    names = {}
    for key, value in (overrides or {}).items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip() or re.search("[A-Za-z]", value):
            raise ValueError("Overrides need nonempty keys and Nepali-script pronunciation values")
        names[key.casefold()] = value
    if names:
        pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(k) for k in sorted(names, key=len, reverse=True)) + r")(?!\w)", re.I)
        text = replace(pattern, lambda m: names[m[0].casefold()], text, "override")
    text = normalize_values(text, replace)
    def latin(match):
        word = match[0]
        if word.isupper() and len(word) > 1:
            after, kind = acronym(word), "acronym"
        elif romanized == "enabled":
            after, kind = transliterate_word(word), "romanized_nepali"
        else:
            after, kind = english_pronunciation(word), "english_pronunciation"
        changes.append({"kind": kind, "before": word, "after": after})
        return after
    text = re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", latin, text)
    cleaned = normalize_punctuation(text)
    if cleaned != text:
        changes.append({"kind": "punctuation", "before": text, "after": cleaned})
    return PreparedText(cleaned, changes)
