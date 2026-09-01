"""Line-by-line INI checker.

Deliberately does not use configparser: in strict mode it raises on the
first duplicate it finds and stops, and in non-strict mode it silently
lets later keys/sections overwrite earlier ones. Neither behavior gives
a full report, and neither tells you the line number of the original
definition. This module walks the file itself so it can report every
problem in one pass, with line numbers for both the duplicate and the
thing it duplicates.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Issue:
    line: int
    severity: str  # "error" or "warning"
    code: str
    message: str


def _find_separator(s: str) -> int:
    for i, ch in enumerate(s):
        if ch in "=:":
            return i
    return -1


def lint(text: str) -> List[Issue]:
    issues: List[Issue] = []
    seen_sections = {}
    section_keys = {}
    current_section: Optional[str] = None
    last_key: Optional[str] = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            last_key = None
            continue

        if stripped.startswith("#") or stripped.startswith(";"):
            continue

        if line != line.rstrip():
            issues.append(Issue(lineno, "warning", "trailing-whitespace", "line has trailing whitespace"))

        indented = line[:1] in (" ", "\t")
        if indented and current_section is not None and last_key is not None:
            # continuation of the previous key's value
            continue

        if stripped.startswith("["):
            last_key = None
            if not stripped.endswith("]"):
                issues.append(Issue(lineno, "error", "malformed-section", f"section header not closed: {stripped!r}"))
                continue
            name = stripped[1:-1].strip()
            if not name:
                issues.append(Issue(lineno, "error", "malformed-section", "section header is empty"))
                continue
            if name in seen_sections:
                issues.append(Issue(
                    lineno, "error", "duplicate-section",
                    f"section [{name}] already defined on line {seen_sections[name]}",
                ))
            else:
                seen_sections[name] = lineno
                section_keys[name] = {}
            current_section = name
            continue

        sep_index = _find_separator(stripped)
        if sep_index == -1:
            issues.append(Issue(
                lineno, "error", "malformed-line",
                f"line is not a comment, section header, or key/value pair: {stripped!r}",
            ))
            last_key = None
            continue

        key = stripped[:sep_index].strip()
        if not key:
            issues.append(Issue(lineno, "error", "malformed-line", "key is empty"))
            last_key = None
            continue

        if current_section is None:
            issues.append(Issue(
                lineno, "warning", "key-outside-section",
                f"key {key!r} appears before any [section] header",
            ))
            target = section_keys.setdefault("", {})
        else:
            target = section_keys[current_section]

        if key in target:
            issues.append(Issue(
                lineno, "error", "duplicate-key",
                f"key {key!r} already defined on line {target[key]} in this section",
            ))
        else:
            target[key] = lineno
        last_key = key

    return issues
