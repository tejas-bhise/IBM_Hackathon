import math
from datetime import datetime

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_RANK  = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

TYPE_LABELS = {
    "SQL_INJECTION":        "SQL Injection Risk",
    "HARDCODED_SECRET":     "Hardcoded Secret / API Key",
    "HARDCODED_PASSWORD":   "Hardcoded Password",
    "PRIVATE_KEY":          "Exposed Private Key",
    "PII_EMAIL":            "Exposed Email Address",
    "PII_PHONE":            "Exposed Phone Number",
    "PII_IN_RESPONSE":      "PII Leaked in API Response",
    "LOG_PII":              "PII Written to Logs",
    "UNSAFE_SERIALIZATION": "Unsafe Deserialization",
    "UNSAFE_PATTERN":       "Unsafe Code Pattern",
}

# Legacy alias kept for any internal callers that used the old name
HUMAN_TYPE_MAP = TYPE_LABELS


def _grade(score: int) -> str:
    if score >= 90: return "A"
    if score >= 80: return "B+"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def build_alerts(issues: list, project_id: str, total_files: int = 1) -> dict:
    """
    Build scored alerts from raw security issues.

    Scoring uses capped per-category penalties so a pile of low-severity issues
    can never push the score to 0.  The workflow engine re-normalises the score
    by repo density — this is the fast initial estimate.

    total_files is accepted for signature compatibility with pipeline.py but
    the capped formula ignores it intentionally (workflow normalises later).
    """
    if not issues:
        return {
            "alerts": [], "security_score": 100, "grade": "A",
            "total_issues": 0, "critical_count": 0, "high_count": 0,
            "medium_count": 0, "low_count": 0,
            "summary": "No security issues detected.", "ai_priority_fix": "",
        }

    confirmed_issues = [i for i in issues if i.get("confirmed", True)]
    if not confirmed_issues:
        return {
            "alerts": [], "security_score": 100, "grade": "A",
            "total_issues": 0, "critical_count": 0, "high_count": 0,
            "medium_count": 0, "low_count": 0,
            "summary": "No confirmed security issues.", "ai_priority_fix": "",
        }

    critical = sum(1 for i in confirmed_issues if i.get("severity") == "CRITICAL")
    high     = sum(1 for i in confirmed_issues if i.get("severity") == "HIGH")
    medium   = sum(1 for i in confirmed_issues if i.get("severity") == "MEDIUM")
    low      = sum(1 for i in confirmed_issues if i.get("severity") == "LOW")

    # Capped penalties — prevents 0 score from sheer volume
    critical_penalty = min(65, critical * 25)
    high_penalty     = min(30, high * 15)
    medium_penalty   = min(10, medium * 7)
    low_penalty      = min(5,  low * 3)
    score = max(5, min(100, 100 - critical_penalty - high_penalty - medium_penalty - low_penalty))
    grade = _grade(score)

    sorted_issues = sorted(
        confirmed_issues,
        key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 3),
    )

    alerts = []
    for issue in sorted_issues:
        raw_type   = issue.get("type", "UNKNOWN")
        type_label = TYPE_LABELS.get(raw_type, raw_type.replace("_", " ").title())
        severity   = (issue.get("severity") or "LOW").upper()
        alerts.append({
            "project_id":     project_id,
            "file_path":      issue.get("file_path", ""),
            "line_number":    issue.get("line_number", 0),
            "type":           raw_type,
            "type_label":     type_label,
            "severity":       severity,
            "severity_rank":  SEVERITY_RANK.get(severity, 4),
            "confirmed":      issue.get("confirmed", True),
            "confidence":     issue.get("confidence", 0.8),
            "explanation":    issue.get("explanation", ""),
            "fix_suggestion": issue.get("fix_suggestion", ""),
            "matched_text":   issue.get("matched_text", "")[:200],
            "code_snippet":   issue.get("code_snippet", "")[:400],
            "before_code":    issue.get("before_code", ""),
            "after_code":     issue.get("after_code", ""),
            "created_at":     datetime.utcnow().isoformat(),
        })

    top_fix      = sorted_issues[0].get("fix_suggestion", "") if sorted_issues else ""
    summary_text = (
        f"{len(alerts)} issue(s): {critical} critical, {high} high, "
        f"{medium} medium, {low} low. Score: {score}/100 ({grade})."
    )

    print(f"   → Alert builder: {len(alerts)} confirmed | C:{critical} H:{high} M:{medium} L:{low} | score={score} ({grade})")

    return {
        "alerts":          alerts,
        "security_score":  score,
        "grade":           grade,
        "total_issues":    len(alerts),
        "critical_count":  critical,
        "high_count":      high,
        "medium_count":    medium,
        "low_count":       low,
        "summary":         summary_text,
        "ai_priority_fix": top_fix,
    }
