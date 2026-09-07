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
    args = parser.parse_args()
    try:
        result = prepare_text(args.text)
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
