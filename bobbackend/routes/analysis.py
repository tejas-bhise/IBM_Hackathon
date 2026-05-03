from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import db.mongo as mongo_db

router = APIRouter()


def _grade(score: int) -> str:
    if score >= 90: return "A"
    if score >= 80: return "B+"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def _recompute_score(critical: int, high: int, medium: int, low: int, total: int) -> int:
    if total == 0:
        return 100
    critical_penalty = min(65, critical * 25)
    high_penalty = min(30, high * 15)
    medium_penalty = min(10, medium * 7)
    low_penalty = min(5, low * 3)
    return max(5, min(100, 100 - critical_penalty - high_penalty - medium_penalty - low_penalty))


def _to_event_objects(items: list, category: str) -> list:
    """Convert plain strings or dicts into structured timeline event objects."""
    result = []
    now = datetime.utcnow().isoformat()
    for item in items:
        if isinstance(item, dict):
            result.append({
                "title": item.get("title", str(item)[:60]),
                "description": item.get("description", str(item)),
                "category": item.get("category", category),
                "timestamp": item.get("timestamp", now),
                "file": item.get("file", ""),
                "line": item.get("line", 0),
            })
        elif isinstance(item, str) and item.strip():
            result.append({
                "title": item[:80],
                "description": item,
                "category": category,
                "timestamp": now,
                "file": "",
                "line": 0,
            })
    return result


def _build_code_stats(summary: dict, issues: list) -> dict:
    tech_stack = summary.get("tech_stack", [])
    modules = summary.get("main_modules", [])
    endpoints = summary.get("api_endpoints", [])

    complexity = "HIGH" if len(modules) > 6 else ("MEDIUM" if len(modules) > 3 else "LOW")

    issue_by_file: dict = {}
    for issue in issues:
        fp = issue.get("file_path", "unknown")
        issue_by_file[fp] = issue_by_file.get(fp, 0) + 1

    hotspot_files = sorted(issue_by_file.items(), key=lambda x: x[1], reverse=True)[:5]

    methods = {}
    for ep in endpoints:
        m = ep.get("method", "GET")
        methods[m] = methods.get(m, 0) + 1

    return {
        "total_modules": len(modules),
        "total_endpoints": len(endpoints),
        "complexity": complexity,
        "hotspot_files": [{"file": f, "issue_count": c} for f, c in hotspot_files],
        "endpoint_methods": methods,
        "has_auth": any(
            "auth" in str(m.get("name", "")).lower() or "jwt" in str(t).lower()
            for m in modules for t in tech_stack
        ),
        "has_database": any(
            x in str(t).lower() for t in tech_stack
            for x in ("postgres", "mongodb", "sqlite", "mysql", "redis")
        ),
        "has_tests": any("test" in str(m.get("name", "")).lower() for m in modules),
    }


@router.get("/analysis/{project_id}")
async def get_analysis(project_id: str):
    # ✅ Pyright Guard
    if mongo_db.projects_col is None:
        raise HTTPException(status_code=500, detail="Database projects_col not initialized")

    project = await mongo_db.projects_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("status") != "completed":
        raise HTTPException(
            status_code=202,
            detail=f"Analysis in progress: {project.get('current_step_name', '')}"
        )

    # ✅ Pyright Guard
    if mongo_db.security_issues_col is None:
        raise HTTPException(status_code=500, detail="Database security_issues_col not initialized")

    issues = await mongo_db.security_issues_col.find(
        {"project_id": project_id}, {"_id": 0}
    ).sort("severity_rank", 1).to_list(length=1000)

    for issue in issues:
        raw_type = issue.get("type", "UNKNOWN")
        label = issue.get("type_label") or raw_type.replace("_", " ").title()
        issue["type_label"] = label
        issue["title"] = issue.get("title") or label
        if not issue.get("explanation") or issue["explanation"] == ":":
            issue["explanation"] = f"Security issue of type {label} detected in {issue.get('file_path', 'unknown file')}."
        if not issue.get("fix_suggestion") or issue["fix_suggestion"] == ":":
            from services.scanner import _default_fix
            issue["fix_suggestion"] = _default_fix(raw_type)

    total_issues = len(issues)
    critical = sum(1 for i in issues if i.get("severity") == "CRITICAL")
    high = sum(1 for i in issues if i.get("severity") == "HIGH")
    medium = sum(1 for i in issues if i.get("severity") == "MEDIUM")
    low = sum(1 for i in issues if i.get("severity") == "LOW")

    score = _recompute_score(critical, high, medium, low, total_issues)
    grade = _grade(score)

    # ✅ Pyright Guards for the remaining find_one calls
    summary = {}
    if mongo_db.project_summaries_col is not None:
        summary = await mongo_db.project_summaries_col.find_one(
            {"project_id": project_id}, {"_id": 0}
        ) or {}

    memory = {}
    if mongo_db.project_memory_col is not None:
        memory = await mongo_db.project_memory_col.find_one(
            {"project_id": project_id}, {"_id": 0}
        ) or {}

    mock = {}
    if mongo_db.mock_data_col is not None:
        mock = await mongo_db.mock_data_col.find_one(
            {"project_id": project_id}, {"_id": 0}
        ) or {}

    workflow = project.get("workflow", {})

    recent_work_events = _to_event_objects(memory.get("recent_work", []), "feature")
    feature_events = _to_event_objects(memory.get("features", []), "feature")
    security_events = _to_event_objects(memory.get("security", []), "security")
    refactor_events = _to_event_objects(memory.get("refactors", []), "refactor")
    all_events = recent_work_events + feature_events + security_events + refactor_events

    code_stats = _build_code_stats(summary, issues)

    return JSONResponse({
        "success": True,
        "project_id": project_id,
        "project_name": project.get("project_name", "Unknown"),
        "total_files_analyzed": project.get("total_files_analyzed", 0),
        "summary": {
            **summary,
            "project_type": summary.get("project_type", "Unknown"),
            "description": summary.get("description", ""),
            "tech_stack": summary.get("tech_stack", []),
            "main_modules": summary.get("main_modules", []),
            "data_flow": summary.get("data_flow", ""),
            "architecture_type": summary.get("architecture_type", summary.get("architecture", "")),
            "api_endpoints": summary.get("api_endpoints", []),
            "entry_point": summary.get("entry_point", "unknown"),
            "security_score": score,
            "grade": grade,
            "total_issues": total_issues,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
        },
        "issues": issues,
        "security_issues": issues,
        "total_issues": total_issues,
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "low_count": low,
        "security_score": score,
        "grade": grade,
        "code_stats": code_stats,
        "memory": {
            "ai_summary": memory.get("ai_summary", ""),
            "recent_work": recent_work_events,
            "features": feature_events,
            "security": security_events,
            "refactors": refactor_events,
            "all_events": all_events,
            "total_events": len(all_events),
            "active_areas": memory.get("active_areas", []),
            "development_phase": memory.get("development_phase", ""),
            "last_focus": memory.get("last_focus", ""),
            "has_git_history": memory.get("has_git_history", False),
            "total_commits_analyzed": memory.get("total_commits_analyzed", 0),
            "commits": memory.get("commits", []),
            "area_map": memory.get("area_map", {}),
        },
        "mock_data": mock,
        "workflow": {
            "stage": workflow.get("stage", ""),
            "stage_label": workflow.get("stage_label", ""),
            "risk_level": workflow.get("risk_level", ""),
            "risk": workflow.get("risk", ""),
            "recommended_action": workflow.get("recommended_action", ""),
            "confidence": workflow.get("confidence", 0),
            "security_score": workflow.get("security_score", score),
            "grade": workflow.get("grade", grade),
            "total_issues": workflow.get("total_issues", total_issues),
            "critical_count": workflow.get("critical_count", critical),
            "high_count": workflow.get("high_count", high),
            "medium_count": workflow.get("medium_count", medium),
            "low_count": workflow.get("low_count", low),
            "blockers": workflow.get("blockers", []),
            "ai_decision": workflow.get("ai_decision", {}),
            "role_views": workflow.get("role_views", {}),
        },
    })