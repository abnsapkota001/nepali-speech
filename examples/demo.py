"""Run the real corpus; record errors and generate mixed_stress when possible."""
import argparse
import json
from pathlib import Path
from nepali_speech import prepare_text
from nepali_speech.transliterate import TransliterationUnavailable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speak", action="store_true")
    args = parser.parse_args()
    corpus = json.loads(Path(__file__).with_name("corpus.json").read_text(encoding="utf-8"))
    report = {}
    for name, text in corpus.items():
        try:
            result = prepare_text(text, romanized="enabled" if name == "romanized_nepali" else "disabled")
            report[name] = {"input": text, "text": result.text, "changes": result.changes, "status": "passed"}
        except TransliterationUnavailable as exc:
            if name != "romanized_nepali":
                raise
            report[name] = {"input": text, "status": "skipped", "reason": str(exc)}
        except (RuntimeError, ImportError, OSError, ValueError) as exc:
            report[name] = {"input": text, "status": "blocked", "error": str(exc)}
        print(name, report[name]["status"], flush=True)
    if args.speak and report["mixed_stress"]["status"] == "passed":
        try:
            from nepali_speech.tts import VITS
            path = VITS().synthesize(report["mixed_stress"]["text"], "outputs/mixed_stress.wav")
            report["mixed_stress"]["wav"] = path.as_posix()
        except (RuntimeError, ImportError, OSError, ValueError) as exc:
            report["mixed_stress"]["status"] = "blocked"
            report["mixed_stress"]["error"] = str(exc)
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/normalization_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if any(row["status"] == "blocked" for row in report.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
