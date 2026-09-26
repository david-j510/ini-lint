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
    parser.add_argument("path", help="path to the .ini file to check, or - to read from stdin")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of plain text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors for the purpose of the exit code",
    )
    args = parser.parse_args(argv)

    from_stdin = args.path == "-"
    display_name = "<stdin>" if from_stdin else args.path
    if from_stdin:
        text = sys.stdin.read()
    else:
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
    severities = {"error"} if not args.strict else {"error", "warning"}
    has_errors = any(issue.severity in severities for issue in issues)

    if args.json:
        payload = {
            "file": display_name,
            "ok": not has_errors,
            "issues": [
                {"line": issue.line, "severity": issue.severity, "code": issue.code, "message": issue.message}
                for issue in issues
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if not issues:
            print(f"{display_name}: no problems found")
        for issue in issues:
            print(f"{display_name}:{issue.line}: {issue.severity}: {issue.message}")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
