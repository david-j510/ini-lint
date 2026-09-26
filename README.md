# inilint

A command-line linter for INI files.

## The problem

The INI format has no formal spec, and most parsers are forgiving about
things that are probably mistakes:

- If a key is defined twice in the same section, Python's `configparser`
  (in its default strict mode) raises `DuplicateOptionError` and stops —
  you fix that one, rerun, and hit the next one. In non-strict mode it
  just keeps the last value and never tells you the first one existed.
- The same goes for a section defined twice.
- A stray line that isn't a comment, a section header, or a `key = value`
  pair is usually a typo (a missing `=`, a copy-pasted fragment) and gets
  silently ignored by most parsers.

`inilint` walks the file once and reports every one of these problems in
a single pass, with line numbers, instead of making you fix them one at
a time.

## Usage

```
$ inilint config.ini
```

Given this file:

```ini
[server]
host = 0.0.0.0
port = 8080
port = 9090

[server]
timeout = 30

not_a_key_value_line
```

output:

```
config.ini:4: error: key 'port' already defined on line 3 in this section
config.ini:6: error: section [server] already defined on line 1
config.ini:9: error: line is not a comment, section header, or key/value pair: 'not_a_key_value_line'
```

The process exits with status `1` if any errors were found, `0` otherwise.
Warnings (like trailing whitespace or a key that appears before any
section header) are reported but don't affect the exit code.

Pass `--strict` to make warnings fail the exit code too, for CI setups
that want zero tolerance instead of just catching outright errors:

```
$ inilint --strict config.ini
```

With `--strict`, `ok` in the JSON output also turns `false` if only
warnings were found.

## Reading from stdin

Pass `-` instead of a file path to read from stdin, useful for piping in
generated config or checking a file before it's written to disk:

```
$ cat config.ini | inilint -
```

The file name in both plain-text and JSON output is reported as
`<stdin>`.

## JSON output

Pass `--json` to get a machine-readable report instead, useful for CI or
for feeding into another tool:

```
$ inilint --json config.ini
```

```json
{
  "file": "config.ini",
  "ok": false,
  "issues": [
    {
      "line": 4,
      "severity": "error",
      "code": "duplicate-key",
      "message": "key 'port' already defined on line 3 in this section"
    },
    {
      "line": 6,
      "severity": "error",
      "code": "duplicate-section",
      "message": "section [server] already defined on line 1"
    },
    {
      "line": 9,
      "severity": "error",
      "code": "malformed-line",
      "message": "line is not a comment, section header, or key/value pair: 'not_a_key_value_line'"
    }
  ]
}
```

`ok` is `true` only when there are no `error`-severity issues (warnings
don't affect it), so a CI step can gate on `.ok` without re-implementing
the exit-code logic.

## Installing

No dependencies beyond the standard library.

```
pip install -e .
```

That gives you the `inilint` command. You can also run it without
installing:

```
python -m inilint config.ini
```

## Checks implemented so far

- `duplicate-section` — a `[section]` header appears more than once
- `duplicate-key` — a key appears more than once in the same section
- `malformed-section` — a section header line isn't properly closed with `]`
- `malformed-line` — a line isn't a comment, section header, or `key = value` pair
- `key-outside-section` (warning) — a key appears before any section header
- `trailing-whitespace` (warning) — a line has trailing spaces or tabs

## License

MIT, see [LICENSE](LICENSE).
