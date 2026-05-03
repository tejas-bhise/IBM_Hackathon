"""
Tests for services/workflow_engine.py
Covers: _determine_stage(), _extract_blockers(),
        _build_dev_view(), _build_pm_view(), _build_investor_view().
All pure / deterministic — no Groq calls.
"""
import pytest
from services.workflow_engine import (
    _determine_stage, _extract_blockers,
    _build_dev_view, _build_pm_view, _build_investor_view,
    STAGE_CONFIG,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _alert_data(score=100, critical=0, high=0, medium=0, low=0, alerts=None):
    return {
        "security_score": score,
        "critical_count": critical,
        "high_count":     high,
        "medium_count":   medium,
        "low_count":      low,
        "total_issues":   critical + high + medium + low,
        "grade":          "A" if score >= 90 else "B+",
        "alerts":         alerts or [],
        "summary":        f"Score: {score}/100",
        "ai_priority_fix": "",
    }


def _alert(severity="CRITICAL", itype="SQL_INJECTION", file_path="app.py", line=1):
    return {
        "severity":      severity,
        "type":          itype,
        "type_label":    itype.replace("_", " ").title(),
        "file_path":     file_path,
        "line_number":   line,
        "fix_suggestion": "Fix it",
        "before_code":   "bad code",
        "after_code":    "good code",
    }


def _summary(project_type="REST API", tech_stack=None, modules=None):
    return {
        "project_type":     project_type,
        "tech_stack":       tech_stack or ["Python", "FastAPI"],
        "main_modules":     modules or [],
        "architecture_type":"monolith",
        "api_endpoints":    [],
        "data_flow":        "client → API → DB",
        "entry_point":      "main.py",
        "missing_features": [],
        "security_features": [],
        "complexity":       "MEDIUM",
    }


def _memory(phase="active_development", focus="API routing"):
    return {
        "development_phase": phase,
        "last_focus":        focus,
        "recent_work":       ["Added auth", "Fixed scanner"],
        "active_areas":      ["routes", "services"],
        "change_categories": {},
    }


def _ai_decision(decision="needs_review", reason="Some reason", priority_fix="Fix X"):
    return {
        "decision":     decision,
        "reason":       reason,
        "priority_fix": priority_fix,
        "confidence":   "medium",
    }


# ── _determine_stage ──────────────────────────────────────────────────────────

class TestDetermineStage:
    def test_critical_blocked_when_critical_ge_1(self):
        assert _determine_stage(_alert_data(critical=1)) == "critical_blocked"

    def test_critical_blocked_overrides_high(self):
        assert _determine_stage(_alert_data(critical=2, high=5)) == "critical_blocked"

    def test_high_risk_when_high_ge_3(self):
        assert _determine_stage(_alert_data(high=3)) == "high_risk"
        assert _determine_stage(_alert_data(high=5)) == "high_risk"

    def test_needs_major_fixes_when_high_1_or_2(self):
        assert _determine_stage(_alert_data(high=1)) == "needs_major_fixes"
        assert _determine_stage(_alert_data(high=2)) == "needs_major_fixes"

    def test_needs_minor_fixes_when_medium_ge_3(self):
        assert _determine_stage(_alert_data(medium=3)) == "needs_minor_fixes"
        assert _determine_stage(_alert_data(medium=5)) == "needs_minor_fixes"

    def test_release_ready_when_score_ge_90(self):
        assert _determine_stage(_alert_data(score=90))  == "release_ready"
        assert _determine_stage(_alert_data(score=100)) == "release_ready"
        assert _determine_stage(_alert_data(score=95))  == "release_ready"

    def test_review_ready_when_score_ge_75(self):
        assert _determine_stage(_alert_data(score=75))  == "review_ready"
        assert _determine_stage(_alert_data(score=80))  == "review_ready"
        assert _determine_stage(_alert_data(score=89))  == "review_ready"

    def test_needs_minor_fixes_when_score_below_75(self):
        assert _determine_stage(_alert_data(score=74))  == "needs_minor_fixes"
        assert _determine_stage(_alert_data(score=50))  == "needs_minor_fixes"
        assert _determine_stage(_alert_data(score=5))   == "needs_minor_fixes"

    def test_clean_project_release_ready(self):
        assert _determine_stage(_alert_data(score=100)) == "release_ready"

    @pytest.mark.parametrize("stage", list(STAGE_CONFIG.keys()))
    def test_all_stages_in_config(self, stage):
        assert stage in STAGE_CONFIG
        assert "label"  in STAGE_CONFIG[stage]
        assert "risk"   in STAGE_CONFIG[stage]
        assert "action" in STAGE_CONFIG[stage]


# ── _extract_blockers ─────────────────────────────────────────────────────────

class TestExtractBlockers:
    def test_critical_extracted(self):
        alerts = [_alert("CRITICAL"), _alert("MEDIUM")]
        blockers = _extract_blockers(alerts)
        assert len(blockers) == 1
        assert blockers[0]["severity"] == "CRITICAL"

    def test_high_extracted(self):
        alerts = [_alert("HIGH")]
        blockers = _extract_blockers(alerts)
        assert len(blockers) == 1
        assert blockers[0]["severity"] == "HIGH"

    def test_medium_and_low_excluded(self):
        alerts = [_alert("MEDIUM"), _alert("LOW")]
        blockers = _extract_blockers(alerts)
        assert len(blockers) == 0

    def test_blocker_has_required_keys(self):
        alerts = [_alert("CRITICAL", file_path="routes/api.py", line=42)]
        blockers = _extract_blockers(alerts)
        assert len(blockers) == 1
        b = blockers[0]
        for key in ("file", "type", "severity", "fix", "line"):
            assert key in b

    def test_file_and_line_preserved(self):
        alerts = [_alert("HIGH", file_path="services/scanner.py", line=99)]
        blockers = _extract_blockers(alerts)
        assert blockers[0]["file"] == "services/scanner.py"
        assert blockers[0]["line"] == 99

    def test_empty_alerts(self):
        assert _extract_blockers([]) == []

    def test_type_label_used_when_present(self):
        alert = _alert("CRITICAL")
        alert["type_label"] = "SQL Injection"
        blockers = _extract_blockers([alert])
        assert blockers[0]["type"] == "SQL Injection"


# ── _build_dev_view ───────────────────────────────────────────────────────────

class TestBuildDevView:
    def test_critical_blocked_status_is_BLOCKED(self):
        ad = _alert_data(critical=1, alerts=[_alert("CRITICAL")])
        view = _build_dev_view(ad, _summary(), "critical_blocked", _ai_decision())
        assert view["status"] == "BLOCKED"

    def test_needs_fixes_status(self):
        ad = _alert_data(high=1, alerts=[_alert("HIGH")])
        view = _build_dev_view(ad, _summary(), "needs_major_fixes", _ai_decision())
        assert "FIX" in view["status"].upper()

    def test_release_ready_status_is_READY(self):
        ad = _alert_data(score=100)
        view = _build_dev_view(ad, _summary(), "release_ready", _ai_decision())
        assert view["status"] == "READY"

    def test_review_ready_status_is_READY(self):
        ad = _alert_data(score=80)
        view = _build_dev_view(ad, _summary(), "review_ready", _ai_decision())
        assert view["status"] == "READY"

    def test_required_keys_present(self):
        ad = _alert_data()
        view = _build_dev_view(ad, _summary(), "release_ready", _ai_decision())
        for key in ("status", "blockers", "issues_to_fix", "total_issues",
                    "tech_stack", "modules", "data_flow", "api_endpoints",
                    "entry_point", "ai_priority_fix", "ai_reason", "action_required"):
            assert key in view, f"Missing key: {key}"

    def test_blockers_populated_for_critical(self):
        ad = _alert_data(critical=1, alerts=[_alert("CRITICAL")])
        view = _build_dev_view(ad, _summary(), "critical_blocked", _ai_decision())
        assert len(view["blockers"]) == 1
        assert view["action_required"] is True

    def test_no_blockers_for_clean_project(self):
        ad = _alert_data(score=100)
        view = _build_dev_view(ad, _summary(), "release_ready", _ai_decision())
        assert view["blockers"] == []
        assert view["action_required"] is False

    def test_tech_stack_from_summary(self):
        ad = _alert_data()
        s  = _summary(tech_stack=["Python", "FastAPI", "MongoDB"])
        view = _build_dev_view(ad, s, "release_ready", _ai_decision())
        assert "Python" in view["tech_stack"]


# ── _build_pm_view ────────────────────────────────────────────────────────────

class TestBuildPmView:
    def test_required_keys_present(self):
        ad  = _alert_data()
        view = _build_pm_view(ad, _summary(), _memory(), "release_ready", _ai_decision())
        for key in ("project_status", "ai_decision", "security_score",
                    "total_open_issues", "critical_issues", "high_issues",
                    "medium_issues", "approval_required", "estimated_release_delay"):
            assert key in view, f"Missing key: {key}"

    def test_critical_blocked_approval_required(self):
        ad  = _alert_data(critical=1)
        view = _build_pm_view(ad, _summary(), _memory(), "critical_blocked", _ai_decision())
        assert view["approval_required"] is True

    def test_release_ready_no_approval(self):
        ad  = _alert_data(score=100)
        view = _build_pm_view(ad, _summary(), _memory(), "release_ready", _ai_decision())
        assert view["approval_required"] is False

    def test_security_score_formatted_as_string(self):
        ad  = _alert_data(score=85)
        view = _build_pm_view(ad, _summary(), _memory(), "review_ready", _ai_decision())
        assert "85" in view["security_score"]

    def test_recent_work_from_memory(self):
        ad  = _alert_data()
        mem = _memory()
        mem["recent_work"] = ["Feature A", "Feature B"]
        view = _build_pm_view(ad, _summary(), mem, "release_ready", _ai_decision())
        assert "Feature A" in view["recent_work"]

    def test_development_phase_from_memory(self):
        ad  = _alert_data()
        view = _build_pm_view(ad, _summary(), _memory(phase="stabilization"),
                              "release_ready", _ai_decision())
        assert view["development_phase"] == "stabilization"


# ── _build_investor_view ──────────────────────────────────────────────────────

class TestBuildInvestorView:
    def test_required_keys_present(self):
        ad  = _alert_data()
        view = _build_investor_view(ad, _summary(), "release_ready", _ai_decision())
        for key in ("project_health_score", "health_label", "release_readiness",
                    "investment_signal", "compliance_risk", "tech_stack",
                    "open_security_issues", "critical_issues"):
            assert key in view, f"Missing key: {key}"

    @pytest.mark.parametrize("score,label", [
        (90, "Excellent"),
        (95, "Excellent"),
        (75, "Good"),
        (80, "Good"),
        (60, "Moderate"),
        (65, "Moderate"),
        (40, "Poor"),
        (55, "Poor"),
        (39, "Critical Risk"),
        (0,  "Critical Risk"),
    ])
    def test_health_label(self, score, label):
        ad = _alert_data(score=score)
        view = _build_investor_view(ad, _summary(), "review_ready", _ai_decision())
        assert view["health_label"] == label, f"score={score} expected {label}"

    def test_compliance_risk_high_when_critical(self):
        ad  = _alert_data(critical=2, score=35)
        view = _build_investor_view(ad, _summary(), "critical_blocked", _ai_decision())
        assert view["compliance_risk"] == "HIGH"

    def test_compliance_risk_medium_when_many_issues(self):
        ad  = _alert_data(score=70, high=2, medium=2)
        view = _build_investor_view(ad, _summary(), "needs_major_fixes", _ai_decision())
        assert view["compliance_risk"] in ("MEDIUM", "HIGH")

    def test_compliance_risk_low_when_clean(self):
        ad  = _alert_data(score=100)
        view = _build_investor_view(ad, _summary(), "release_ready", _ai_decision())
        assert view["compliance_risk"] == "LOW"

    def test_release_readiness_for_release_ready(self):
        ad  = _alert_data(score=100)
        view = _build_investor_view(ad, _summary(), "release_ready", _ai_decision())
        assert "Production Ready" in view["release_readiness"]

    def test_investment_signal_green_for_release_ready(self):
        ad  = _alert_data(score=100)
        view = _build_investor_view(ad, _summary(), "release_ready", _ai_decision())
        assert "GREEN" in view["investment_signal"]

    def test_investment_signal_red_for_critical_blocked(self):
        ad  = _alert_data(critical=1, score=35)
        view = _build_investor_view(ad, _summary(), "critical_blocked", _ai_decision())
        assert "RED" in view["investment_signal"]

    def test_tech_stack_passed_through(self):
        s   = _summary(tech_stack=["Python", "MongoDB"])
        ad  = _alert_data()
        view = _build_investor_view(ad, s, "release_ready", _ai_decision())
        assert "Python" in view["tech_stack"]
