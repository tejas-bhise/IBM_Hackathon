"""
Tests for services/alert_builder.py
Covers: _grade(), build_alerts() score formula, confirmed filtering,
        severity counts, type_label mapping, capped penalties.
"""
import pytest
from services.alert_builder import _grade, build_alerts, TYPE_LABELS


# ── _grade ─────────────────────────────────────────────────────────────────────

class TestGrade:
    def test_grade_A_boundary(self):
        assert _grade(90) == "A"

    def test_grade_A_above(self):
        assert _grade(100) == "A"
        assert _grade(95)  == "A"

    def test_grade_Bplus(self):
        assert _grade(80) == "B+"
        assert _grade(85) == "B+"
        assert _grade(89) == "B+"

    def test_grade_B(self):
        assert _grade(70) == "B"
        assert _grade(75) == "B"
        assert _grade(79) == "B"

    def test_grade_C(self):
        assert _grade(60) == "C"
        assert _grade(65) == "C"
        assert _grade(69) == "C"

    def test_grade_D(self):
        assert _grade(50) == "D"
        assert _grade(55) == "D"
        assert _grade(59) == "D"

    def test_grade_F(self):
        assert _grade(49)  == "F"
        assert _grade(0)   == "F"
        assert _grade(5)   == "F"


# ── build_alerts — score formula ───────────────────────────────────────────────

class TestBuildAlertsScore:

    def _make_issue(self, severity, itype="SQL_INJECTION"):
        return {
            "confirmed": True,
            "severity":  severity,
            "type":      itype,
            "file_path": "app.py",
            "line_number": 1,
            "matched_text": "x",
            "code_snippet": "x",
            "explanation": "",
            "fix_suggestion": "",
            "before_code": "",
            "after_code":  "",
        }

    def test_zero_issues_returns_100(self):
        result = build_alerts([], "proj1")
        assert result["security_score"] == 100
        assert result["grade"] == "A"
        assert result["total_issues"] == 0

    def test_unconfirmed_issues_excluded(self):
        issues = [{"confirmed": False, "severity": "CRITICAL", "type": "SQL_INJECTION"}]
        result = build_alerts(issues, "proj1")
        assert result["total_issues"] == 0
        assert result["security_score"] == 100

    def test_one_critical_penalty(self):
        # 1 critical: penalty = min(65, 1*25) = 25  →  score = max(5, 75) = 75
        result = build_alerts([self._make_issue("CRITICAL")], "proj1")
        assert result["security_score"] == 75
        assert result["critical_count"] == 1

    def test_two_critical_one_high(self):
        # 2 critical: min(65, 50)=50  |  1 high: min(30, 15)=15  →  100-50-15=35
        issues = [
            self._make_issue("CRITICAL"),
            self._make_issue("CRITICAL"),
            self._make_issue("HIGH", "HARDCODED_PASSWORD"),
        ]
        result = build_alerts(issues, "proj1")
        assert result["security_score"] == 35
        assert result["critical_count"] == 2
        assert result["high_count"]     == 1

    def test_critical_penalty_capped_at_65(self):
        # 4 criticals: 4*25=100 → capped at 65  →  score = max(5, 100-65) = 35
        issues = [self._make_issue("CRITICAL")] * 4
        result = build_alerts(issues, "proj1")
        assert result["critical_count"] == 4
        assert result["security_score"] == 35  # 100 - 65 = 35

    def test_high_penalty_capped_at_30(self):
        # 3 high: 3*15=45 → capped at 30  →  score = max(5, 100-30) = 70
        issues = [self._make_issue("HIGH", "HARDCODED_PASSWORD")] * 3
        result = build_alerts(issues, "proj1")
        assert result["high_count"]     == 3
        assert result["security_score"] == 70

    def test_score_never_below_5_with_issues(self):
        # Max penalties: 65 + 30 + 10 + 5 = 110  →  100-110 = -10  →  max(5, -10) = 5
        issues = (
            [self._make_issue("CRITICAL")] * 4 +
            [self._make_issue("HIGH", "HARDCODED_PASSWORD")] * 3 +
            [self._make_issue("MEDIUM", "PII_EMAIL")] * 2 +
            [self._make_issue("LOW", "PII_PHONE")] * 2
        )
        result = build_alerts(issues, "proj1")
        assert result["security_score"] >= 5

    def test_medium_and_low_counts(self):
        issues = [
            self._make_issue("MEDIUM", "PII_EMAIL"),
            self._make_issue("LOW",    "PII_PHONE"),
        ]
        result = build_alerts(issues, "proj1")
        assert result["medium_count"] == 1
        assert result["low_count"]    == 1


# ── build_alerts — alert structure ────────────────────────────────────────────

class TestBuildAlertsStructure:

    def _confirmed(self, severity="CRITICAL", itype="PRIVATE_KEY"):
        return {
            "confirmed":     True,
            "severity":      severity,
            "type":          itype,
            "file_path":     "secrets.py",
            "line_number":   7,
            "matched_text":  "-----BEGIN RSA PRIVATE KEY-----",
            "code_snippet":  "key = '-----BEGIN RSA PRIVATE KEY-----'",
            "explanation":   "Private key exposed",
            "fix_suggestion":"Revoke and move to vault",
            "before_code":   "key = '...'",
            "after_code":    "key = os.environ['PRIVATE_KEY']",
        }

    def test_alert_has_required_keys(self):
        result = build_alerts([self._confirmed()], "proj1")
        alert  = result["alerts"][0]
        for key in ("project_id","file_path","line_number","type","type_label",
                    "severity","severity_rank","fix_suggestion","created_at"):
            assert key in alert, f"Missing key: {key}"

    def test_type_label_resolved(self):
        result = build_alerts([self._confirmed("CRITICAL", "PRIVATE_KEY")], "proj1")
        assert result["alerts"][0]["type_label"] == TYPE_LABELS["PRIVATE_KEY"]

    def test_unknown_type_label_fallback(self):
        issue = self._confirmed("HIGH", "SOME_NEW_TYPE")
        result = build_alerts([issue], "proj1")
        assert result["alerts"][0]["type_label"] == "Some New Type"

    def test_severity_rank_critical_is_1(self):
        result = build_alerts([self._confirmed("CRITICAL")], "proj1")
        assert result["alerts"][0]["severity_rank"] == 1

    def test_matched_text_truncated_to_200(self):
        issue = self._confirmed()
        issue["matched_text"] = "x" * 300
        result = build_alerts([issue], "proj1")
        assert len(result["alerts"][0]["matched_text"]) <= 200

    def test_summary_string_present(self):
        result = build_alerts([self._confirmed()], "proj1")
        assert "score" in result["summary"].lower()

    def test_result_keys(self):
        result = build_alerts([], "proj1")
        for k in ("alerts","security_score","grade","total_issues",
                  "critical_count","high_count","medium_count","low_count","summary"):
            assert k in result
