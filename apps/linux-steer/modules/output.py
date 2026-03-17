"""JSON output formatting — matches macOS steer schema exactly."""

import json
import sys


def emit(data: dict, *, as_json: bool = False, human_lines: str = "") -> None:
    if as_json:
        json.dump(data, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if human_lines:
            sys.stdout.write(human_lines)
            if not human_lines.endswith("\n"):
                sys.stdout.write("\n")


def emit_error(message: str, *, as_json: bool = False) -> None:
    data = {"ok": False, "error": message}
    if as_json:
        json.dump(data, sys.stderr, indent=2)
        sys.stderr.write("\n")
    else:
        sys.stderr.write(f"Error: {message}\n")
    raise SystemExit(1)
