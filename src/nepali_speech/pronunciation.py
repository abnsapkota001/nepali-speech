"""Overrides, letter names, and approximate English phoneme rendering."""
from functools import lru_cache
import os
from pathlib import Path
import re

LETTERS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "ए|बी|सी|डी|ई|एफ|जी|एच|आई|जे|के|एल|एम|एन|ओ|पी|क्यू|आर|एस|टी|यू|भी|डब्ल्यू|एक्स|वाई|जेड".split("|")))
CONSONANTS = dict(zip(
    "B CH D DH F G HH JH K L M N NG P R S SH T TH V W Y Z ZH".split(),
    "ब च ड द फ ग ह ज क ल म न ङ प र स श ट थ भ व य ज झ".split(),
))
VOWELS = {
    "AA": ("आ", "ा"), "AE": ("आ", "ा"), "AH": ("अ", ""),
    "AO": ("अ", ""), "AW": ("आउ", "ाउ"), "AY": ("आइ", "ाइ"),
    "EH": ("ए", "े"), "ER": ("अर", "र"), "EY": ("ए", "े"),
    "IH": ("इ", "ि"), "IY": ("ई", "ी"), "OW": ("ओ", "ो"),
    "OY": ("ओइ", "ोइ"), "UH": ("उ", "ु"), "UW": ("ऊ", "ू"),
}


def acronym(word):
    return " ".join(LETTERS[c] for c in word)


def pronunciation_resources(*, download=False):
    """Check NLTK data, downloading only when explicitly requested."""
    cache = Path(os.environ.get("NEPALI_SPEECH_CACHE", "outputs/.cache")) / "nltk"
    os.environ.setdefault("NLTK_DATA", str(cache.resolve()))
    import nltk
    if str(cache.resolve()) not in nltk.data.path:
        nltk.data.path.insert(0, str(cache.resolve()))
    # g2p_en checks both archives during import, even though we do not tag POS.
    for resource, location in (("cmudict", "corpora/cmudict.zip"), ("averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger.zip")):
        try:
            nltk.data.find(location)
        except LookupError:
            if not download:
                raise RuntimeError("Pronunciation data missing. Run: nepali-speech setup-pronunciation") from None
            cache.mkdir(parents=True, exist_ok=True)
            if not nltk.download(resource, download_dir=str(cache), quiet=True):
                raise RuntimeError(f"Unable to download NLTK resource {resource}")


@lru_cache(maxsize=1)
def _g2p():
    pronunciation_resources()
    from g2p_en import G2p
    return G2p()


@lru_cache(maxsize=2048)
def english_pronunciation(word):
    engine = _g2p()
    # Word-level dictionary lookup or neural prediction; no POS tagging.
    phones = engine.cmu.get(word.lower())
    phones = phones[0] if phones else engine.predict(word.lower())
    return phonemes_to_nepali(phones)


def phonemes_to_nepali(phones):
    """Render ARPAbet with consonant clusters and context-sensitive vowels.

    AE uses the Nepali loanword approximation आ; it is distinct from EH (ए).
    Rhotic AO uses ओ, medial unstressed IY shortens, and IY before a vowel
    becomes a य glide. No word-specific pronunciation substitutions are used.
    """
    out = ""
    pending = False
    for index, raw in enumerate(phones):
        phone = re.sub(r"\d", "", raw)
        following = re.sub(r"\d", "", phones[index + 1]) if index + 1 < len(phones) else None
        if phone == "IY" and following in VOWELS:
            phone = "Y"
        if phone in CONSONANTS:
            if pending:
                out += "्"
            out += CONSONANTS[phone]
            pending = True
        elif phone in VOWELS:
            independent, dependent = VOWELS[phone]
            if phone == "AO" and following == "R":
                independent, dependent = "ओ", "ो"
            elif raw == "IY0" and following in CONSONANTS:
                independent, dependent = "इ", "ि"
            out += dependent if pending else independent
            # ER ends in र; a following schwa belongs to that consonant.
            pending = phone == "ER"
        else:
            raise ValueError(f"Unsupported English phoneme: {raw}")
    if not out:
        raise ValueError("No pronunciation phonemes")
    return out
