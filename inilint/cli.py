import argparse
import json
import sys
from pathlib import Path

from .parser import lint


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="inilint",
        description="Check an INI file for duplicate sections, duplicate keys, and structural problems.",
    )
    parser.add_argument("path", help="path to the .ini file to check")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of plain text")
    args = parser.parse_args(argv)

    file_path = Path(args.path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        if args.json:
            print(json.dumps({"file": args.path, "ok": False, "issues": [], "error": str(exc)}))
        else:
            print(f"inilint: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    issues = lint(text)
    has_errors = any(issue.severity == "error" for issue in issues)

    if args.json:
        payload = {
            "file": str(file_path),
            "ok": not has_errors,
            "issues": [
                {"line": issue.line, "severity": issue.severity, "code": issue.code, "message": issue.message}
                for issue in issues
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if not issues:
            print(f"{file_path}: no problems found")
        for issue in issues:
            print(f"{file_path}:{issue.line}: {issue.severity}: {issue.message}")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
