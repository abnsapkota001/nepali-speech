# Nepali Speech — Local Nepali Text-to-Speech (TTS) Toolkit

**Nepali Speech** is an open-source Python toolkit for Nepali text-to-speech (TTS), speech preprocessing, and local speech synthesis.

It prepares real-world Nepali and mixed Nepali-English text for speech by handling numbers, dates, currency, English words, acronyms, punctuation, pronunciation overrides, and optional Romanized Nepali transliteration. It also includes local Nepali speech generation using a VITS model.

Useful for Nepali TTS, Nepali AI voice applications, accessibility, news/audio generation, voice assistants, and other Nepali-language AI projects.

## Key features

- Nepali text-to-speech preprocessing
- Local Nepali VITS speech synthesis
- Mixed Nepali-English text normalization
- Nepali number, date, and currency normalization
- English-to-Nepali pronunciation handling
- Acronym pronunciation
- Optional Romanized Nepali → Devanagari transliteration
- Custom pronunciation overrides
- Fully local inference after model setup

## 30-second demo

After installation and pronunciation setup:

```sh
nepali-speech normalize 'Kathmandu मा Nov 5 मा हुने music festival को ticket $30 हुनेछ।'
```

```sh
nepali-speech speak 'Kathmandu मा Nov 5 मा हुने music festival को ticket $30 हुनेछ।' -o demo.wav
```

## Features

- Spoken Nepali integers, whole-dollar USD amounts, and English month/day dates.
- Generic English pronunciation with g2p_en and letter-by-letter acronyms.
- Caller-provided word and phrase overrides; no built-in word dictionary.
- Optional Romanized Nepali transliteration and local VITS speech.
- An ordered list of text changes. Postpositions stay separate for TTS, and `।`
  becomes `.` without manually inserted audio silence.

Before: `Kathmandu मा Nov 5 मा हुने music festival को ticket $30 हुनेछ।`

After: `काठमाडौं मा नोभेम्बर पाँच तारिख मा हुने म्युजिक फेस्टिभल को टिकट तीस अमेरिकी डलर हुनेछ.`

## Install

Requires Python 3.10+.

### Core package

```sh
python -m venv .venv
# Activate .venv using your shell.
python -m pip install -e .
nepali-speech setup-pronunciation

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
Enable it explicitly with `prepare_text(text, romanized="enabled")` or
`--romanized enabled` on the CLI. The default `disabled` mode treats Latin words
as English and never loads IndicXlit. Overrides and acronyms take precedence.

The `nepali_speech.transliterate.transliterate_word` interface raises
`TransliterationUnavailable` when the optional backend is missing. Only explicitly
requested transliteration needs it; optional integration tests skip when absent.

## VITS

Install `python -m pip install -e ".[tts]"` before using `speak` or:

```python
from nepali_speech.tts import VITS

VITS().synthesize(result.text, "outputs/demo.wav")
```

Text preparation never loads VITS. English pronunciation data is downloaded only
by `nepali-speech setup-pronunciation`; normalization reports missing data without
downloading it. Nepali text, numbers, and acronyms need no pronunciation setup.

First synthesis downloads pinned VITS source and weights; cached inference runs
locally on CPU.
Caches default to `outputs/.cache`; set `NEPALI_SPEECH_CACHE` to change this.
Generated audio, environments, and model caches are excluded from Git.

## Limitations

English phoneme rendering is approximate, and homographs use the first dictionary
pronunciation. Supply overrides for preferred names or pronunciations. Romanized
Nepali must be enabled explicitly for Latin words in the input. Dates support month/day without calendar validation;
decimals and grouped numbers are unsupported. Uppercase Latin words spell out as
acronyms. VITS may warn about unsupported characters and omit them.

## Roadmap

Improve pronunciation, simplify optional IndicXlit installation, and support more
numeric formats. Vendor and minimize the upstream VITS code executed at runtime.

MIT license for package code. Dependencies and downloaded
[Nepali VITS weights](https://huggingface.co/Dragneel/nepali-vits-tts) retain their
own licenses. VITS inference uses [upstream source](https://github.com/jaywalnut310/vits).
