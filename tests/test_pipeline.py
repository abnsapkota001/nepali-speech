import json
from pathlib import Path
import subprocess
import sys

import pytest
from nepali_speech import prepare_text
from nepali_speech import pipeline
from nepali_speech.pronunciation import acronym
from nepali_speech.transliterate import TransliterationUnavailable

CORPUS = json.loads((Path(__file__).parents[1] / "examples/corpus.json").read_text(encoding="utf-8"))

@pytest.fixture(autouse=True)
def offline_english(monkeypatch):
    from nepali_speech import pronunciation
    class Engine:
        cmu = json.loads((Path(__file__).parent / "fixtures/english_phonemes.json").read_text(encoding="utf-8"))
    pronunciation.english_pronunciation.cache_clear()
    monkeypatch.setattr(pronunciation, "_g2p", lambda: Engine())
    yield
    pronunciation.english_pronunciation.cache_clear()

@pytest.mark.parametrize("name", list(CORPUS))
def test_corpus(name):
    # Generic rendering uses recorded phoneme fixtures; no model downloads.
    try:
        result = prepare_text(CORPUS[name])
    except TransliterationUnavailable as exc:
        if name == "T6":
            pytest.skip(str(exc))
        raise
    assert not any(c.isascii() and c.isalpha() for c in result.text)
    assert "।" not in result.text
    assert result.changes
    if name == "T1":
        assert result.text == CORPUS[name].replace("।", ".")
    if name == "T2":
        assert "एक सय पच्चीस" in result.text
        assert "बीस अमेरिकी डलर" in result.text
    if name in {"T3", "T7"}:
        assert "टोक्यो मा अक्टोबर बाह्र तारिख मा" in result.text
    if name in {"T4", "T7"}:
        assert "ट्राभल" in result.text
        assert "ट्रेभल" not in result.text
    if name == "T5":
        assert "बी बी सी" in result.text and "डब्ल्यू एच ओ" in result.text
    if name == "T6":
        assert sum(c["kind"] == "romanized_nepali" for c in result.changes) == 6
    if name == "T7":
        assert "चालीस अमेरिकी डलर" in result.text


def test_custom_override_precedence():
    result = prepare_text("Tokyo र tokyo", overrides={"Tokyo": "टोकियो"})
    assert result.text == "टोकियो र टोकियो"
    assert result.changes == [{"kind": "override", "before": "Tokyo", "after": "टोकियो"}, {"kind": "override", "before": "tokyo", "after": "टोकियो"}]


def test_override_boundaries(monkeypatch):
    monkeypatch.setattr(pipeline, "english_pronunciation", lambda word: "अन्य")
    assert prepare_text("Tokyotown", overrides={"Tokyo": "टोकियो"}).text == "अन्य"


def test_acronyms():
    assert prepare_text("BBC WHO").text == "बी बी सी डब्ल्यू एच ओ"
    assert acronym("XYZ") == "एक्स वाई जेड"


@pytest.mark.parametrize("month", ["September", "Sept", "Sep", "sept."])
def test_date_aliases(month):
    assert prepare_text(month + " 7").text == "सेप्टेम्बर सात तारिख"


@pytest.mark.parametrize("text", ["Sept 0", "Sept 32", "$2.50", "1,000"])
def test_unsupported_values(text):
    with pytest.raises(ValueError):
        prepare_text(text)


def test_number_and_currency():
    assert prepare_text("25 $25 २५").text == "पच्चीस पच्चीस अमेरिकी डलर पच्चीस"


def test_punctuation():
    assert prepare_text("आज। भोलि? पर्सि!").text == "आज. भोलि. पर्सि."


def test_no_vits_import():
    subprocess.run([sys.executable, "-c", "from nepali_speech import prepare_text; prepare_text('25'); import sys; assert 'torch' not in sys.modules; assert 'nepali_speech.tts' not in sys.modules"], check=True)


def test_missing_indicxlit_is_explicit(monkeypatch):
    def unavailable(word):
        raise TransliterationUnavailable("unavailable")
    monkeypatch.setattr(pipeline, "transliterate_word", unavailable)
    with pytest.raises(TransliterationUnavailable):
        prepare_text(CORPUS["T6"])


def test_empty_and_type():
    assert prepare_text("").text == ""
    assert prepare_text("").changes == []
    with pytest.raises(TypeError):
        prepare_text(None)


@pytest.mark.parametrize("phones,expected", [
    (["T", "R", "AE1", "V", "AH0", "L"], "ट्राभल"),
    (["K", "AE1", "T"], "काट"),
    (["K", "AA1", "N", "F", "ER0", "AH0", "N", "S"], "कान्फरन्स"),
    (["K", "EH1", "T"], "केट"),
    (["R", "IY0", "P", "AO1", "R", "T"], "रिपोर्ट"),
    (["T", "OW1", "K", "IY0", "OW2"], "टोक्यो"),
])
def test_generic_phoneme_mapping(phones, expected):
    from nepali_speech.pronunciation import phonemes_to_nepali
    assert phonemes_to_nepali(phones) == expected


def test_developer_override_and_spacing():
    result = prepare_text("Tokyo मा travel को ticket।", overrides={"Tokyo": "टोकियो", "travel": "ट्र्याभल"})
    assert result.text == "टोकियो मा ट्र्याभल को टिकट."
    assert [c["kind"] for c in result.changes].count("override") == 2


def test_transliteration_interface(monkeypatch):
    from nepali_speech import transliterate
    class Engine:
        def translit_word(self, word, topk):
            assert word == "pokhara" and topk == 1
            return {"ne": ["पोखरा"]}
    transliterate.transliterate_word.cache_clear()
    monkeypatch.setattr(transliterate, "_engine", lambda: Engine())
    assert transliterate.transliterate_word("pokhara") == "पोखरा"
    transliterate.transliterate_word.cache_clear()


def test_phrase_override_longest_match():
    result = prepare_text("MUSIC festival र Music", overrides={"music": "सङ्गीत", "Music Festival": "सङ्गीत महोत्सव"})
    assert result.text == "सङ्गीत महोत्सव र सङ्गीत"
    assert all(c["kind"] == "override" for c in result.changes)


def test_override_precedes_acronym_and_transliteration(monkeypatch):
    def unexpected(word):
        pytest.fail("Caller override must bypass automatic pronunciation")
    monkeypatch.setattr(pipeline, "transliterate_word", unexpected)
    monkeypatch.setattr(pipeline, "english_pronunciation", unexpected)
    assert prepare_text("BBC aaja hotel", overrides={"bbc": "समाचार", "aaja": "आज", "hotel": "होटेल"}).text == "समाचार आज होटेल"


def test_no_builtin_word_overrides(monkeypatch):
    calls = []
    def pronounce(word):
        calls.append(word)
        return "शब्द"
    monkeypatch.setattr(pipeline, "english_pronunciation", pronounce)
    assert prepare_text("Texas Dallas Diaspora United Airlines USCIS").text == "शब्द शब्द शब्द शब्द शब्द यू एस सी आई एस"
    assert calls == ["Texas", "Dallas", "Diaspora", "United", "Airlines"]
