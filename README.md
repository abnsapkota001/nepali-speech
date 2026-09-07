# nepali-speech

Prepare mixed Nepali text for speech. Numbers, Latin words, and punctuation can
otherwise be misread or dropped by a Nepali TTS model.

## Features

- Spoken Nepali integers, whole-dollar USD amounts, and English month/day dates.
- Generic English pronunciation with g2p_en and letter-by-letter acronyms.
- Caller-provided word and phrase overrides; no built-in word dictionary.
- Optional Romanized Nepali transliteration and local VITS speech.
- An ordered list of text changes. Postpositions stay separate for TTS, and `।`
  becomes `.` without manually inserted audio silence.

Before: `Tokyo मा Oct 12 मा $40 हुनेछ।`

After: `टोक्यो मा अक्टोबर बाह्र तारिख मा चालीस अमेरिकी डलर हुनेछ.`

## Install

Requires Python 3.10+. Clone this repository, then install from its directory:

```sh
python -m venv .venv
# Activate .venv using your shell.
python -m pip install -e .
```

For development: `python -m pip install -e ".[dev]"`, then `python -m pytest`.
Tests use phoneme fixtures and need no TTS models or pronunciation downloads.

## API

```python
from nepali_speech import prepare_text

result = prepare_text("Tokyo मा Oct 12 मा ticket $40 हुनेछ.")
print(result.text)
print(result.changes)

custom = prepare_text(
    "Music Festival मा travel",
    overrides={"music festival": "सङ्गीत महोत्सव", "travel": "ट्र्याभल"},
)
```

Overrides match whole words or phrases case-insensitively; the longest match
wins. They take precedence over acronyms and automatic pronunciation.
`changes` records each transformation's `kind`, `before`, and `after`.

## CLI

Single quotes preserve dollar amounts in PowerShell:

```sh
nepali-speech normalize 'Tokyo मा Oct 12 मा ticket $40 हुनेछ.' --changes
nepali-speech speak 'Tokyo मा Oct 12 मा ticket $40 हुनेछ.' -o outputs/demo.wav
```

## Optional IndicXlit

Install `python -m pip install -e ".[indicxlit]"` for Romanized Nepali.
The lazy `nepali_speech.transliterate.transliterate_word` interface is retained.
Without a working backend, it raises `TransliterationUnavailable`; optional
transliteration tests skip with a reason. Core features work without IndicXlit.
Its older fairseq dependencies may not install on newer Python versions.

## VITS

Install `python -m pip install -e ".[tts]"` before using `speak` or:

```python
from nepali_speech.tts import VITS

VITS().synthesize(result.text, "outputs/demo.wav")
```

Text preparation never loads VITS. First use downloads the required NLTK
resources or VITS source and weights; cached inference runs locally on CPU.
Caches default to `outputs/.cache`; set `NEPALI_SPEECH_CACHE` to change this.
Generated audio, environments, and model caches are excluded from Git.

## Limitations

English phoneme rendering is approximate, and homographs use the first dictionary
pronunciation. Supply overrides for preferred names or pronunciations. Romanized
Nepali detection is heuristic. Dates support month/day without calendar validation;
decimals and grouped numbers are unsupported. Uppercase Latin words spell out as
acronyms. VITS may warn about unsupported characters and omit them.

## Roadmap

Improve pronunciation, simplify optional IndicXlit installation, and support more
numeric formats.

MIT license for package code. Dependencies and downloaded
[Nepali VITS weights](https://huggingface.co/Dragneel/nepali-vits-tts) retain their
own licenses. VITS inference uses [upstream source](https://github.com/jaywalnut310/vits).
