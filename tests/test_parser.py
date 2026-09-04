import unittest

from inilint.parser import lint


def codes(text):
    return [issue.code for issue in lint(text)]


class LintTests(unittest.TestCase):
    def test_clean_file_has_no_issues(self):
        text = "[server]\nhost = 0.0.0.0\nport = 8080\n"
        self.assertEqual(lint(text), [])

    def test_duplicate_section(self):
        text = "[server]\nhost = a\n\n[server]\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["duplicate-section"])
        issue = issues[0]
        self.assertEqual(issue.line, 4)
        self.assertEqual(issue.severity, "error")
        self.assertIn("already defined on line 1", issue.message)

    def test_duplicate_key(self):
        text = "[server]\nport = 8080\nport = 9090\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["duplicate-key"])
        issue = issues[0]
        self.assertEqual(issue.line, 3)
        self.assertEqual(issue.severity, "error")
        self.assertIn("already defined on line 2", issue.message)

    def test_duplicate_key_scoped_per_section(self):
        text = "[a]\nkey = 1\n\n[b]\nkey = 2\n"
        self.assertEqual(codes(text), [])

    def test_malformed_section_unclosed(self):
        text = "[server\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["malformed-section"])
        self.assertEqual(issues[0].line, 1)

    def test_malformed_section_empty_name(self):
        text = "[]\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["malformed-section"])
        self.assertEqual(issues[0].line, 1)

    def test_malformed_line_no_separator(self):
        text = "[server]\nnot_a_key_value_line\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["malformed-line"])
        self.assertEqual(issues[0].line, 2)

    def test_malformed_line_empty_key(self):
        text = "[server]\n = value\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["malformed-line"])
        self.assertEqual(issues[0].line, 2)

    def test_key_outside_section(self):
        text = "host = a\n\n[server]\nport = 8080\n"
        issues = lint(text)
        self.assertEqual(codes(text), ["key-outside-section"])
        issue = issues[0]
        self.assertEqual(issue.line, 1)
        self.assertEqual(issue.severity, "warning")

    def test_trailing_whitespace(self):
        text = "[server]\nhost = a  \n"
        issues = lint(text)
        self.assertEqual(codes(text), ["trailing-whitespace"])
        issue = issues[0]
        self.assertEqual(issue.line, 2)
        self.assertEqual(issue.severity, "warning")

    def test_comments_are_ignored(self):
        text = "; comment\n# also a comment\n[server]\nhost = a\n"
        self.assertEqual(codes(text), [])

    def test_colon_separator_supported(self):
        text = "[server]\nhost: 0.0.0.0\n"
        self.assertEqual(codes(text), [])

    def test_indented_continuation_line_not_flagged(self):
        text = "[server]\ndescription = first line\n    second line\n"
        self.assertEqual(codes(text), [])


if __name__ == "__main__":
    unittest.main()
