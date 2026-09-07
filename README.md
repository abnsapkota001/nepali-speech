# nepali-speech

Prepare mixed Nepali text for local VITS speech. Raw digits, Latin words, and
Devanagari danda punctuation can otherwise be misread or dropped by the model.

**V1:** T1–T5 and T7 are verified with local Windows CPU VITS.
Romanized Nepali uses the optional IndicXlit adapter. Core installation works
without it; T6 runs when available and skips with a reason otherwise. The
adapter interface is tested, but live IndicXlit output is unverified here.

## Features

- Nepali number words, whole-dollar USD amounts, and English month/day dates.
- Caller pronunciation overrides, acronyms, and approximate English phonetics.
- Optional IndicXlit support for Romanized Nepali.
- Sentence punctuation and an ordered audit list of transformations.
- Local CPU VITS synthesis with no manually inserted silence.

Before: `Tokyo मा Oct 12 मा $40 हुनेछ।`

After: `टोक्यो मा अक्टोबर बाह्र तारिख मा चालीस अमेरिकी डलर हुनेछ.`

## Installation

From this directory, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e '.[tts,dev]'
```

Text-only installation: `python -m pip install -e .`.
The existing local environment is `.venv`; if venv's pip bootstrap fails,
`python -m pip --python .venv\Scripts\python.exe install -e '.[tts,dev]'`
uses the host's pip to install into it.

Optional Romanized Nepali support: `python -m pip install -e ".[indicxlit]"`.
Its legacy fairseq stack failed to build in this Windows/Python 3.13 environment.
T6 skips with that backend unavailable; all core features work without it.
`nepali_speech.transliterate.transliterate_word` remains available as the lazy
transliteration interface and raises `TransliterationUnavailable` if needed.

The first English conversion downloads NLTK resources. First synthesis downloads
VITS source and weights if absent. Later cached inference is local.
All runtime caches default to `outputs/.cache` relative to the current directory;
set `NEPALI_SPEECH_CACHE` to choose another location. No VITS model is loaded by
`prepare_text`.

## API

```python
from nepali_speech import prepare_text

result = prepare_text("Tokyo मा Oct 12 मा ticket $40 हुनेछ.")
print(result.text)
print(result.changes)

# Case-insensitive, whole-word or phrase replacements; longest match wins.
custom = prepare_text("Tokyo मा travel", overrides={"Tokyo": "टोकियो", "travel": "ट्र्याभल"})

from nepali_speech.tts import VITS
VITS().synthesize(result.text, "outputs/demo.wav")
```

`result` contains only `text` and `changes`. Each change contains `kind`, `before`,
and `after`; the list describes transformations in execution order, not offsets.
Resolution is override → acronym → likely Romanized Nepali via IndicXlit →
English via g2p_en. Routing hints are a small heuristic, not a language detector.
English rendering uses generic ARPAbet rules, not a growing word dictionary.
AE maps to आ separately from EH (ए), so `travel` becomes `ट्राभल`; vowel
glides and rhotic vowels are handled in context. Developer overrides take
precedence for preferred pronunciations. Existing five legacy overrides remain
for compatibility; the neutral corpus requires none.

Spacing is TTS-first: postpositions remain separate (`टोक्यो मा`), and `।`
becomes `.` without manually added audio silence.

## CLI

Use single quotes in PowerShell to preserve `$40` literally.

```powershell
nepali-speech normalize 'Tokyo मा Oct 12 मा ticket $40 हुनेछ.' --changes
nepali-speech speak 'Tokyo मा Oct 12 मा ticket $40 हुनेछ.' -o outputs/demo.wav
```

## Demo and tests

```powershell
python -m pytest -q
python examples/demo.py --speak
```

`examples/corpus.json` contains the seven exact requested texts. The demo records
real output/errors in `outputs/normalization_report.json` and writes T7 audio to
`outputs/t7_demo.wav` (22,050 Hz mono). T6 skips only when IndicXlit is
unavailable. The demo exits nonzero if another case fails. Corpus tests and the
demo exercise real English pronunciation; small unit tests cover phoneme rules
and the optional adapter interface. No human listening review is claimed.
Generated outputs, weights, environments, and caches are excluded from Git.

## Limitations

- Optional IndicXlit (T6) is skipped when unavailable.
- English phoneme-to-Devanagari rendering is approximate; homographs use the first
  dictionary pronunciation. Foreign names may need caller overrides.
- Dates support month + day 1–31, without year or calendar validation.
- Numbers support standalone integers; decimals and grouped numbers raise errors.
- Acronyms are uppercase Latin tokens; uppercase ordinary words also spell out.
- VITS may omit unsupported symbols with a warning. No audio quality score or
  human listening review is claimed.

## Roadmap

Future work: optional IndicXlit packaging and native-speaker T6 review,
improved English phoneme rendering, and more numeric formats.

## Sources and license

Package code: MIT, see LICENSE. Downloaded dependencies, model weights, and source
retain their own licenses and are not included in the package license.

- [Nepali VITS model](https://huggingface.co/Dragneel/nepali-vits-tts)
- [Upstream VITS](https://github.com/jaywalnut310/vits)
- [nepali-num2word](https://pypi.org/project/nepali-num2word/)
- [AI4Bharat IndicXlit](https://github.com/AI4Bharat/IndicXlit)
- [g2p_en](https://github.com/Kyubyong/g2p)

Source is available on GitHub. No PyPI publication.
