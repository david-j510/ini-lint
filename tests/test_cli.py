import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inilint.cli import main


def run(*args):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(list(args))
    return code, stdout.getvalue()


def run_with_stdin(text, *args):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout), mock.patch("sys.stdin", io.StringIO(text)):
        code = main(list(args))
    return code, stdout.getvalue()


class CliTests(unittest.TestCase):
    def _write(self, text):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False)
        tmp.write(text)
        tmp.close()
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        return tmp.name

    def test_clean_file_exits_zero(self):
        path = self._write("[server]\nhost = 0.0.0.0\n")
        code, out = run(path)
        self.assertEqual(code, 0)
        self.assertIn("no problems found", out)

    def test_error_exits_one(self):
        path = self._write("[server]\nport = 1\nport = 2\n")
        code, out = run(path)
        self.assertEqual(code, 1)
        self.assertIn("already defined on line 2", out)

    def test_warning_only_exits_zero_without_strict(self):
        path = self._write("key = 1\n")
        code, out = run(path)
        self.assertEqual(code, 0)

    def test_warning_only_exits_one_with_strict(self):
        path = self._write("key = 1\n")
        code, out = run("--strict", path)
        self.assertEqual(code, 1)

    def test_strict_has_no_effect_when_already_erroring(self):
        path = self._write("[server]\nport = 1\nport = 2\n")
        plain_code, _ = run(path)
        strict_code, _ = run("--strict", path)
        self.assertEqual(plain_code, strict_code)

    def test_json_ok_false_for_warning_only_in_strict_mode(self):
        path = self._write("key = 1\n")
        code, out = run("--json", "--strict", path)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(code, 1)

    def test_json_ok_true_for_warning_only_without_strict(self):
        path = self._write("key = 1\n")
        code, out = run("--json", path)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(code, 0)

    def test_missing_file_exits_two(self):
        code, out = run("/no/such/file.ini")
        self.assertEqual(code, 2)

    def test_stdin_dash_reads_from_stdin(self):
        code, out = run_with_stdin("[server]\nport = 1\nport = 2\n", "-")
        self.assertEqual(code, 1)
        self.assertIn("<stdin>", out)
        self.assertIn("already defined on line 2", out)

    def test_stdin_dash_clean_input(self):
        code, out = run_with_stdin("[server]\nhost = 0.0.0.0\n", "-")
        self.assertEqual(code, 0)
        self.assertIn("<stdin>: no problems found", out)

    def test_stdin_dash_json(self):
        code, out = run_with_stdin("key = 1\n", "--json", "-")
        payload = json.loads(out)
        self.assertEqual(payload["file"], "<stdin>")
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
