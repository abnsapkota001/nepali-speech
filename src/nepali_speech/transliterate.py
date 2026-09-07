"""Lazy AI4Bharat IndicXlit adapter for Romanized Nepali."""
from functools import lru_cache
import re


class TransliterationUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _engine():
    try:
        from ai4bharat.transliteration import XlitEngine
        return XlitEngine("ne", beam_width=4, rescore=False)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        raise TransliterationUnavailable(
            "IndicXlit is unavailable. Install the indicxlit extra in a compatible "
            "environment; Romanized Nepali cannot be reliably processed without it."
        ) from exc


@lru_cache(maxsize=2048)
def transliterate_word(word):
    candidates = _engine().translit_word(word.lower(), topk=1)
    if isinstance(candidates, dict):
        candidates = candidates.get("ne", [])
    if not candidates or not re.search(r"[\u0900-\u097f]", candidates[0]):
        raise TransliterationUnavailable(f"IndicXlit returned no Nepali candidate for {word!r}")
    return candidates[0]


# Routing hints, not pronunciation substitutions. IndicXlit generates the output.
_HINTS = set("aaja aja ma ko ka ki lai le ra chha cha ho nepali namaste hunechha thulo sano samudayako karyakram bholi mero timro hami tapai ramro garnu huncha chhan".split())


def likely_romanized(word, context):
    words = re.findall(r"[A-Za-z]+", context.lower())
    return word.lower() in _HINTS or (sum(w in _HINTS for w in words) >= 2 and word.islower())
