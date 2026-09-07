"""Command-line entry points."""
import argparse
import json
from . import prepare_text


def main():
    parser = argparse.ArgumentParser(prog="nepali-speech")
    commands = parser.add_subparsers(dest="command", required=True)
    normal = commands.add_parser("normalize")
    normal.add_argument("text")
    normal.add_argument("--changes", action="store_true")
    speak = commands.add_parser("speak")
    speak.add_argument("text")
    speak.add_argument("-o", "--output", required=True)
    commands.add_parser("setup-pronunciation", help="Download English pronunciation data")
    for command in (normal, speak):
        command.add_argument("--romanized", choices=("enabled", "disabled"), default="disabled")
    args = parser.parse_args()
    try:
        if args.command == "setup-pronunciation":
            from .pronunciation import pronunciation_resources
            pronunciation_resources(download=True)
            return
        result = prepare_text(args.text, romanized=args.romanized)
        if args.command == "normalize":
            print(result.text)
            if args.changes:
                print(json.dumps(result.changes, ensure_ascii=False, indent=2))
        else:
            from .tts import VITS
            print(VITS().synthesize(result.text, args.output))
    except (RuntimeError, ValueError, ImportError, OSError) as exc:
        parser.exit(1, f"nepali-speech: {exc}\n")


if __name__ == "__main__":
    main()
