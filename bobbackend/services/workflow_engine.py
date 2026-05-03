"""
Pure rule-based workflow engine — ZERO LLM calls.
All signal comes from score + issue counts already computed by alert_builder.

Exposes the hackathon-compatible testable interface:
  STAGE_CONFIG, _determine_stage, _extract_blockers,
  _build_dev_view, _build_pm_view, _build_investor_view
while keeping bobbackend's density-aware scoring and returning all
field names both the frontend and test suite expect.
"""
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Stage config (6 levels, hackathon naming) ─────────────────────────────────
STAGE_CONFIG = {
    "critical_blocked":  {"label": "🔴 BLOCKED — Critical Issues",          "risk": "critical", "action": "stop_and_fix"},
    "high_risk":         {"label": "🟠 HIGH RISK — Needs Immediate Fixes",   "risk": "high",     "action": "urgent_fix_required"},
    "needs_major_fixes": {"label": "🟠 Needs Major Fixes Before Release",    "risk": "high",     "action": "dev_fix_required"},
    "needs_minor_fixes": {"label": "🟡 Almost Ready — Minor Fixes Required", "risk": "medium",   "action": "dev_fix_recommended"},
    "review_ready":      {"label": "🟢 Review Ready — Low Risk",             "risk": "low",      "action": "pm_review_recommended"},
    "release_ready":     {"label": "✅ Release Ready",                        "risk": "none",     "action": "approve_for_release"},
}


# ── Density-aware scoring (authoritative — overwrites alert_builder) ──────────
def _compute_score(critical: int, high: int, medium: int, low: int, total_files: int = 1) -> tuple:
    raw_penalty  = (critical * 30) + (high * 10) + (medium * 3) + (low * 1)
    total_issues = critical + high + medium + low
    if total_issues == 0 or raw_penalty == 0:
        return 100, "A"
    files_factor = max(1, min(total_files, 500))
    density      = total_issues / files_factor
    scale        = min(1.0, 0.3 + (density * 1.4))
    ep           = raw_penalty * scale
    score        = max(5, round(100 - (ep * (1 - math.exp(-ep / 100)))))
    if   score >= 90: grade = "A"
    elif score >= 80: grade = "B+"
    elif score >= 75: grade = "B"
    elif score >= 60: grade = "C"
    elif score >= 40: grade = "D"
    else:             grade = "F"
    return score, grade


# ── Stage determination ───────────────────────────────────────────────────────
def _determine_stage(alert_data: dict) -> str:
    score    = alert_data.get("security_score", 100)
    critical = alert_data.get("critical_count", 0)
    high     = alert_data.get("high_count", 0)
    medium   = alert_data.get("medium_count", 0)
    if critical >= 1: return "critical_blocked"
    if high >= 3:     return "high_risk"
    if high >= 1:     return "needs_major_fixes"
    if medium >= 3:   return "needs_minor_fixes"
    if score >= 90:   return "release_ready"
    if score >= 75:   return "review_ready"
    return "needs_minor_fixes"


# ── Blocker extraction ────────────────────────────────────────────────────────
def _extract_blockers(alerts: list) -> list:
    return [
        {
            "file":     a.get("file_path", ""),
            "type":     a.get("type_label", a.get("type", "")),
            "severity": a.get("severity", ""),
            "fix":      a.get("fix_suggestion", ""),
            "line":     a.get("line_number", 0),
        }
        for a in alerts if a.get("severity") in ("CRITICAL", "HIGH")
    ]


# ── Role views ────────────────────────────────────────────────────────────────
def _build_dev_view(alert_data: dict, summary: dict, stage: str, ai_decision: dict) -> dict:
    alerts   = alert_data.get("alerts", [])
    blockers = _extract_blockers(alerts)
    if stage == "critical_blocked":  status = "BLOCKED"
    elif "fix" in stage:             status = "NEEDS FIXES"
    else:                            status = "READY"

    return {
        "status":            status,
        "blockers":          blockers,
        "issues_to_fix": [
            {
                "file":     a.get("file_path", ""),
                "line":     a.get("line_number", 0),
                "type":     a.get("type_label", a.get("type", "")),
                "severity": a.get("severity", ""),
                "fix":      a.get("fix_suggestion", ""),
                "before":   a.get("before_code", ""),
                "after":    a.get("after_code", ""),
            }
            for a in alerts
        ],
        "total_issues":      alert_data.get("total_issues", 0),
        "tech_stack":        summary.get("tech_stack", []),
        "modules": [
            {
                "name":             m.get("name", ""),
                "key_files":        m.get("key_files", []),
                "purpose":          m.get("purpose", ""),
                "responsibilities": m.get("responsibilities", ""),
                "depends_on":       m.get("depends_on", ""),
            }
            for m in summary.get("main_modules", [])
        ],
        "data_flow":         summary.get("data_flow", ""),
        "architecture":      summary.get("architecture_type", summary.get("architecture", "Unknown")),
        "api_endpoints":     summary.get("api_endpoints", [])[:20],
        "entry_point":       summary.get("entry_point", ""),
        "missing_features":  summary.get("missing_features", []),
        "security_features": summary.get("security_features", []),
        "ai_priority_fix":   ai_decision.get("priority_fix", alert_data.get("ai_priority_fix", "")),
        "ai_reason":         ai_decision.get("reason", alert_data.get("summary", "")),
        "action_required":   len(blockers) > 0,
    }


def _build_pm_view(alert_data: dict, summary: dict, memory: dict, stage: str, ai_decision: dict) -> dict:
    critical = alert_data.get("critical_count", 0)
    high     = alert_data.get("high_count", 0)
    medium   = alert_data.get("medium_count", 0)
    score    = alert_data.get("security_score", 100)
    grade    = alert_data.get("grade", "A")

    status_map = {
        "critical_blocked":  "🔴 BLOCKED — Critical issues must be resolved",
        "high_risk":         "🟠 AT RISK — High severity issues require attention",
        "needs_major_fixes": "🟠 AT RISK — Significant issues need resolution",
        "needs_minor_fixes": "🟡 ALMOST READY — Minor fixes required",
        "review_ready":      "🟢 IN REVIEW — Awaiting final sign-off",
        "release_ready":     "✅ READY FOR RELEASE",
    }
    delay_map = {
        "critical_blocked":  "Blocked until critical issues resolved",
        "high_risk":         f"3–5 days (fix {high} high severity issue(s))",
        "needs_major_fixes": f"2–3 days (fix {high} high issue(s))",
        "needs_minor_fixes": f"< 1 day (fix {medium} medium issue(s))",
        "review_ready":      "Ready for staging — no delay",
        "release_ready":     "No delay — approved",
    }

    return {
        "project_status":          status_map.get(stage, "Unknown"),
        "ai_decision":             ai_decision.get("decision", "needs_review" if alert_data.get("total_issues", 0) > 0 else "approved"),
        "ai_reasoning":            ai_decision.get("reason", f"Score {score}/100 ({grade}). {alert_data.get('total_issues', 0)} issue(s)."),
        "estimated_release_delay": delay_map.get(stage, "Unknown"),
        "security_score":          f"{score}/100 ({grade})",
        "total_open_issues":       alert_data.get("total_issues", 0),
        "critical_issues":         critical,
        "high_issues":             high,
        "medium_issues":           medium,
        "feature_modules":         [str(m.get("name", "")) for m in summary.get("main_modules", [])],
        "api_count":               len(summary.get("api_endpoints", [])),
        "recent_work":             memory.get("recent_work", []),
        "development_phase":       memory.get("development_phase", "active_development"),
        "last_developer_focus":    memory.get("last_focus", ""),
        "active_areas":            memory.get("active_areas", []),
        "project_type":            summary.get("project_type", "Unknown"),
        "missing_features":        summary.get("missing_features", []),
        "approval_required":       stage in ("critical_blocked", "high_risk", "needs_major_fixes"),
    }


def _build_investor_view(alert_data: dict, summary: dict, stage: str, ai_decision: dict) -> dict:
    score    = alert_data.get("security_score", 100)
    grade    = alert_data.get("grade", "A")
    total    = alert_data.get("total_issues", 0)
    critical = alert_data.get("critical_count", 0)

    if   score >= 90: health_label = "Excellent"
    elif score >= 75: health_label = "Good"
    elif score >= 60: health_label = "Moderate"
    elif score >= 40: health_label = "Poor"
    else:             health_label = "Critical Risk"

    readiness_map = {
        "release_ready":     "✅ Production Ready",
        "review_ready":      "🟢 Near Ready — Minor cleanup",
        "needs_minor_fixes": "🟡 Not Ready — Minor fixes needed",
        "needs_major_fixes": "🟠 Not Ready — Significant issues",
        "high_risk":         "🟠 Not Ready — High risk",
        "critical_blocked":  "🔴 Blocked — Critical security issues",
    }
    signal_map = {
        "release_ready":     "GREEN — Low risk, strong execution",
        "review_ready":      "GREEN — Strong foundation, minor gaps",
        "needs_minor_fixes": "YELLOW — Promising but needs polish",
        "needs_major_fixes": "YELLOW/RED — Execution risk present",
        "high_risk":         "RED — Do not release without fixes",
        "critical_blocked":  "RED — Critical risk, do not invest until resolved",
    }

    return {
        "project_health_score": score,
        "grade":                grade,
        "health_label":         health_label,
        "release_readiness":    readiness_map.get(stage, "Unknown"),
        "investment_signal":    signal_map.get(stage, "YELLOW"),
        "ai_decision":          ai_decision.get("decision", "needs_review" if total > 0 else "approved"),
        "ai_reasoning":         ai_decision.get("reason", f"Score {score}/100 ({grade}). {total} issues total."),
        "open_security_issues": total,
        "critical_issues":      critical,
        "tech_stack":           summary.get("tech_stack", []),
        "project_type":         summary.get("project_type", "Unknown"),
        "architecture":         summary.get("architecture_type", summary.get("architecture", "Unknown")),
        "complexity":           summary.get("complexity", "HIGH" if len(summary.get("main_modules", [])) > 6 else "MEDIUM"),
        "api_surface":          len(summary.get("api_endpoints", [])),
        "compliance_risk": (
            "HIGH"   if critical > 0 else
            "MEDIUM" if total > 3   else "LOW"
        ),
        "missing_features":     summary.get("missing_features", []),
    }


# ── Main entry point ──────────────────────────────────────────────────────────
async def build_workflow(alert_data: dict, summary: dict, memory: dict) -> dict:
    critical    = alert_data.get("critical_count", 0)
    high        = alert_data.get("high_count",     0)
    medium      = alert_data.get("medium_count",   0)
    low         = alert_data.get("low_count",      0)
    total_files = memory.get("total_files", 1)

    # Density-aware score overwrites alert_builder's initial estimate
    score, grade = _compute_score(critical, high, medium, low, total_files)
    alert_data["security_score"] = score
    alert_data["grade"]          = grade

    stage = _determine_stage(alert_data)
    cfg   = STAGE_CONFIG[stage]

    # Deterministic ai_decision — rule-based confidence, no LLM spend
    ai_decision = {
        "decision":     "rejected" if stage in ("critical_blocked", "high_risk") else (
                        "needs_review" if stage in ("needs_major_fixes", "needs_minor_fixes") else "approved"),
        "reason":       (
            f"Security score {score}/100 ({grade}). "
            f"{critical} critical, {high} high, {medium} medium issues. "
            f"Stage: {stage}."
        ),
        "priority_fix": alert_data.get("ai_priority_fix", ""),
        "confidence":   "high" if score >= 90 else ("medium" if score >= 60 else "low"),
    }

    dev_view = _build_dev_view(alert_data, summary, stage, ai_decision)
    pm_view  = _build_pm_view(alert_data, summary, memory, stage, ai_decision)
    inv_view = _build_investor_view(alert_data, summary, stage, ai_decision)

    print(
        f"✅ Workflow [rule-based]: stage={stage} | "
        f"score={score} ({grade}) | risk={cfg['risk']}"
    )

    return {
        # Core fields
        "stage":              stage,
        "stage_label":        cfg["label"],
        "risk":               cfg["risk"],          # primary — routes/workflow.py reads this
        "risk_level":         cfg["risk"],          # alias for frontend compat
        "action":             cfg["action"],        # routes/workflow.py reads this
        "recommended_action": cfg["action"],        # alias
        "security_score":     score,
        "grade":              grade,
        "total_issues":       alert_data.get("total_issues", 0),
        "critical_count":     critical,
        "high_count":         high,
        "medium_count":       medium,
        "low_count":          low,
        "blockers":           _extract_blockers(alert_data.get("alerts", [])),
        "summary":            alert_data.get("summary", ""),
        "confidence":         round(score / 100, 2),
        "ai_decision":        ai_decision,
        "computed_at":        datetime.utcnow().isoformat(),
        "mode":               "rule-based",
        # Flat role views (routes/workflow.py reads dev_view / pm_view / investor_view)
        "dev_view":           dev_view,
        "pm_view":            pm_view,
        "investor_view":      inv_view,
        # Nested alias for any consumer that uses role_views.dev etc.
        "role_views": {
            "dev":      dev_view,
            "pm":       pm_view,
            "investor": inv_view,
        },
    }
