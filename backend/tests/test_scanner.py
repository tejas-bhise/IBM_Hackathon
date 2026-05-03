"""
Tests for services/scanner.py
Covers: _is_test_file(), _is_example_file(), _get_snippet(),
        _confirm_issues(), _default_fix(), _run_regex_pass() patterns,
        AUTO_CONFIRM types, test-file PII handling.
All tests are pure (no Groq calls, no async).
"""
import pytest
from services.scanner import (
    _is_test_file, _is_example_file, _get_snippet, _confirm_issues,
    _default_fix, _run_regex_pass, PATTERNS, TYPE_SEVERITY, AUTO_CONFIRM,
)


# ── _is_test_file ──────────────────────────────────────────────────────────────

class TestIsTestFile:
    @pytest.mark.parametrize("path,expected", [
        ("test/auth.py",              True),
        ("tests/scanner.py",          True),
        ("test_auth.py",              True),
        ("auth.test.js",              True),
        ("auth.spec.ts",              True),
        ("__test__/helpers.py",       True),
        ("fixture/data.py",           True),
        ("mock/users.py",             True),
        ("examples/demo.py",          True),
        ("services/scanner.py",       False),
        ("routes/upload.py",          False),
        ("main.py",                   False),
        ("db/mongo.py",               False),
    ])
    def test_classification(self, path, expected):
        assert _is_test_file(path) == expected, f"Failed for path: {path}"


# ── _is_example_file ──────────────────────────────────────────────────────────

class TestIsExampleFile:
    @pytest.mark.parametrize("path,expected", [
        (".env.example",         True),
        ("config.sample.py",     True),
        ("template.yaml",        True),
        ("README.md",            True),
        ("services/scanner.py",  False),
        ("main.py",              False),
    ])
    def test_classification(self, path, expected):
        assert _is_example_file(path) == expected


# ── _get_snippet ───────────────────────────────────────────────────────────────

class TestGetSnippet:
    def test_returns_tuple(self):
        content = "line1\nline2\nline3\n"
        snippet, line_num = _get_snippet(content, 0)
        assert isinstance(snippet, str)
        assert isinstance(line_num, int)

    def test_line_number_is_one_indexed(self):
        content = "line1\nline2\nline3\n"
        _, line_num = _get_snippet(content, 0)
        assert line_num >= 1

    def test_match_at_start_no_underflow(self):
        content = "SELECT * FROM users WHERE id = " + "user_id\n" + "x\n" * 10
        snippet, line_num = _get_snippet(content, 0)
        assert line_num == 1
        assert "SELECT" in snippet

    def test_match_in_middle(self):
        lines = ["line1", "line2", "MATCH_HERE", "line4", "line5", "line6", "line7"]
        content = "\n".join(lines)
        match_start = content.index("MATCH_HERE")
        snippet, line_num = _get_snippet(content, match_start)
        assert "MATCH_HERE" in snippet
        assert line_num == 3

    def test_context_lines_included(self):
        lines = [f"line{i}" for i in range(20)]
        content = "\n".join(lines)
        match_start = content.index("line10")
        snippet, _ = _get_snippet(content, match_start)
        assert len(snippet.split("\n")) >= 2


# ── _confirm_issues ────────────────────────────────────────────────────────────

class TestConfirmIssues:
    def _issue(self, confidence):
        return {"type": "PII_EMAIL", "confidence": confidence, "confirmed": True}

    def test_high_confidence_kept(self):
        issues = [self._issue(0.9), self._issue(1.0), self._issue(0.8)]
        result = _confirm_issues(issues)
        assert len(result) == 3

    def test_low_confidence_also_kept(self):
        issues = [self._issue(0.5), self._issue(0.3), self._issue(0.1)]
        result = _confirm_issues(issues)
        assert len(result) == 3

    def test_empty_input(self):
        assert _confirm_issues([]) == []


# ── _default_fix ───────────────────────────────────────────────────────────────

class TestDefaultFix:
    @pytest.mark.parametrize("itype,keyword", [
        ("SQL_INJECTION",        "parameterized"),
        ("HARDCODED_SECRET",     "environment"),
        ("HARDCODED_PASSWORD",   "environment"),
        ("PRIVATE_KEY",          "REVOKE"),
        ("PII_EMAIL",            "environment"),
        ("PII_PHONE",            "fake"),
        ("PII_IN_RESPONSE",      "PII"),
        ("LOG_PII",              "log"),
        ("UNSAFE_SERIALIZATION", "pickle"),
    ])
    def test_fix_contains_keyword(self, itype, keyword):
        fix = _default_fix(itype)
        assert keyword.lower() in fix.lower(), f"Expected '{keyword}' in fix for {itype}"

    def test_unknown_type_returns_owasp(self):
        fix = _default_fix("UNKNOWN_TYPE")
        assert "OWASP" in fix


# ── _run_regex_pass — pattern matching ────────────────────────────────────────

class TestRunRegexPass:

    def _file(self, path, content):
        return {"path": path, "content": content, "extension": ".py"}

    def test_private_key_auto_confirmed(self):
        content = "key = '-----BEGIN RSA PRIVATE KEY-----\n...'"
        findings = _run_regex_pass([self._file("config.py", content)])
        pkey = [f for f in findings if f["type"] == "PRIVATE_KEY"]
        assert len(pkey) >= 1
        assert pkey[0]["confirmed"] is True
        assert pkey[0]["severity"] == "CRITICAL"
        assert pkey[0]["needs_ai"] is False

    def test_unsafe_serialization_auto_confirmed(self):
        content = "data = pickle.loads(untrusted_bytes)"
        findings = _run_regex_pass([self._file("utils.py", content)])
        found = [f for f in findings if f["type"] == "UNSAFE_SERIALIZATION"]
        assert len(found) >= 1
        assert found[0]["confirmed"] is True
        assert found[0]["needs_ai"] is False

    def test_sql_injection_needs_ai(self):
        content = "query = 'SELECT * FROM users WHERE id = ' + user_id"
        findings = _run_regex_pass([self._file("db.py", content)])
        sql = [f for f in findings if f["type"] == "SQL_INJECTION"]
        assert len(sql) >= 1
        assert sql[0]["needs_ai"] is True
        assert sql[0]["confirmed"] is False

    def test_hardcoded_password_needs_ai(self):
        content = "password = 'mysecret123'"
        findings = _run_regex_pass([self._file("config.py", content)])
        pwd = [f for f in findings if f["type"] == "HARDCODED_PASSWORD"]
        assert len(pwd) >= 1
        assert pwd[0]["needs_ai"] is True

    def test_hardcoded_secret_detected(self):
        content = "api_key = 'sk-" + "A" * 25 + "'"
        findings = _run_regex_pass([self._file("config.py", content)])
        secrets = [f for f in findings if f["type"] == "HARDCODED_SECRET"]
        assert len(secrets) >= 1

    def test_hardcoded_secret_skipped_in_example_file(self):
        content = "OPENAI_KEY=sk-" + "A" * 25
        findings = _run_regex_pass([self._file(".env.example", content)])
        secrets = [f for f in findings if f["type"] == "HARDCODED_SECRET"]
        assert len(secrets) == 0

    def test_email_in_test_file_is_low(self):
        content = "user = {'email': 'john@example.com'}"
        findings = _run_regex_pass([self._file("tests/test_auth.py", content)])
        emails = [f for f in findings if f["type"] == "PII_EMAIL"]
        assert len(emails) >= 1
        assert emails[0]["severity"] == "LOW"
        assert emails[0]["confirmed"] is True
        assert emails[0]["needs_ai"] is False

    def test_phone_in_test_file_is_low(self):
        content = "phone = '9876543210'"
        findings = _run_regex_pass([self._file("tests/test_user.py", content)])
        phones = [f for f in findings if f["type"] == "PII_PHONE"]
        assert len(phones) >= 1
        assert phones[0]["severity"] == "LOW"

    def test_yaml_load_unsafe(self):
        content = "data = yaml.load(stream)"
        findings = _run_regex_pass([self._file("parser.py", content)])
        found = [f for f in findings if f["type"] == "UNSAFE_SERIALIZATION"]
        assert len(found) >= 1

    def test_clean_file_no_findings(self):
        content = "def add(a, b):\n    return a + b\n"
        findings = _run_regex_pass([self._file("utils.py", content)])
        assert findings == []

    def test_empty_file_no_findings(self):
        findings = _run_regex_pass([self._file("empty.py", "")])
        assert findings == []

    def test_multiple_files(self):
        files = [
            self._file("a.py", "key = '-----BEGIN RSA PRIVATE KEY-----'"),
            self._file("b.py", "def safe(): return 1"),
        ]
        findings = _run_regex_pass(files)
        assert len(findings) >= 1

    def test_finding_structure(self):
        content = "key = '-----BEGIN RSA PRIVATE KEY-----'"
        findings = _run_regex_pass([self._file("sec.py", content)])
        assert len(findings) >= 1
        f = findings[0]
        for key in ("file_path","line_number","type","matched_text",
                    "code_snippet","needs_ai","confirmed","confidence"):
            assert key in f, f"Missing key: {key}"

    def test_confidence_is_float_between_0_and_1(self):
        content = "key = '-----BEGIN RSA PRIVATE KEY-----'"
        findings = _run_regex_pass([self._file("sec.py", content)])
        for f in findings:
            assert 0.0 <= f["confidence"] <= 1.0


# ── Pattern sanity checks ─────────────────────────────────────────────────────

class TestPatterns:
    def test_email_pattern_matches(self):
        assert PATTERNS["PII_EMAIL"].search("user@example.com")

    def test_email_pattern_no_false_positive(self):
        assert not PATTERNS["PII_EMAIL"].search("not_an_email")

    def test_private_key_pattern_matches(self):
        assert PATTERNS["PRIVATE_KEY"].search("-----BEGIN RSA PRIVATE KEY-----")
        assert PATTERNS["PRIVATE_KEY"].search("-----BEGIN PRIVATE KEY-----")
        assert PATTERNS["PRIVATE_KEY"].search("-----BEGIN EC PRIVATE KEY-----")

    def test_hardcoded_password_matches(self):
        assert PATTERNS["HARDCODED_PASSWORD"].search("password = 'secret123'")
        assert PATTERNS["HARDCODED_PASSWORD"].search('password: "hunter2"')

    def test_hardcoded_password_no_short_value(self):
        assert not PATTERNS["HARDCODED_PASSWORD"].search("pwd = 'ab'")

    def test_unsafe_serialization_pickle(self):
        assert PATTERNS["UNSAFE_SERIALIZATION"].search("pickle.loads(data)")

    def test_unsafe_serialization_yaml_load(self):
        assert PATTERNS["UNSAFE_SERIALIZATION"].search("yaml.load(stream)")

    def test_hardcoded_secret_openai(self):
        assert PATTERNS["HARDCODED_SECRET"].search("sk-" + "A" * 25)

    def test_hardcoded_secret_aws(self):
        assert PATTERNS["HARDCODED_SECRET"].search("AKIA" + "A" * 16)
