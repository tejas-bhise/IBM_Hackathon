from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import db.mongo as mongo_db

router = APIRouter()


def _to_event_objects(items: list, category: str) -> list:
    """
    ✅ FIX: Memory service saves items as plain strings.
    Frontend expects objects: {title, description, category, timestamp}
    This converts bare strings into proper event objects so the timeline renders.
    """
    result = []
    now = datetime.utcnow().isoformat()
    for item in items:
        if isinstance(item, dict):
            # Already an object — ensure all required fields exist
            result.append({
                "title": item.get("title", str(item)[:60]),
                "description": item.get("description", str(item)),
                "category": item.get("category", category),
                "timestamp": item.get("timestamp", now),
                "file": item.get("file", ""),
                "line": item.get("line", 0),
            })
        elif isinstance(item, str) and item.strip():
            # Plain string — wrap into structured object
            result.append({
                "title": item[:80],
                "description": item,
                "category": category,
                "timestamp": now,
                "file": "",
                "line": 0,
            })
    return result


@router.get("/memory/{project_id}")
async def get_memory(project_id: str):
    """
    Get project memory timeline with recent work, features, security, and refactors.
    Returns structured memory data for the frontend timeline view.
    """
    # ✅ Pyright Guard: Ensure collection is not None
    if mongo_db.projects_col is None:
        raise HTTPException(status_code=500, detail="Database projects_col not initialized")

    project = await mongo_db.projects_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("status") != "completed":
        raise HTTPException(status_code=202, detail="Analysis not yet complete")

    # ✅ Pyright Guard: Ensure collection is not None
    if mongo_db.project_memory_col is None:
        raise HTTPException(status_code=500, detail="Database project_memory_col not initialized")

    memory = await mongo_db.project_memory_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )

    if not memory:
        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "recent_work": [],
            "features": [],
            "security": [],
            "refactors": [],
            "commits": [],
            "all_events": [],
            "total_events": 0,
            "ai_summary": "",
            "active_areas": [],
            "development_phase": "unknown",
            "last_focus": "",
            "has_git_history": False,
            "total_commits_analyzed": 0,
            "area_map": {},
            "mode": "empty",
        })

    # ✅ All items → structured event objects
    recent_work = _to_event_objects(memory.get("recent_work", []), "feature")
    features = _to_event_objects(memory.get("features", []), "feature")
    security = _to_event_objects(memory.get("security", []), "security")
    refactors = _to_event_objects(memory.get("refactors", []), "refactor")

    # Build all_events merged timeline
    all_events = recent_work + features + security + refactors

    # Add commits as timeline events
    commits = memory.get("commits", [])
    for commit in commits[:10]:
        if isinstance(commit, dict) and commit.get("message"):
            all_events.append({
                "title": f"Commit: {commit.get('message', '')[:60]}",
                "description": (
                    f"{commit.get('message', '')} "
                    f"by {commit.get('author', 'Unknown')} "
                    f"({commit.get('hash', '')[:8]})"
                ),
                "category": "commit",
                "timestamp": commit.get("timestamp", datetime.utcnow().isoformat()),
                "file": "",
                "line": 0,
            })

    # ✅ NEW: area_map — maps feature areas to files (for "Codebase Areas" section)
    area_map = memory.get("area_map", {})

    # ✅ NEW: Build "active files" section from commits/mtime
    active_files = []
    seen_files: set = set()
    for commit in commits[:15]:
        msg = commit.get("message", "")
        if msg and msg not in seen_files and not msg.startswith("Commit:"):
            seen_files.add(msg)
            active_files.append({
                "file": msg,
                "last_seen": commit.get("timestamp", ""),
                "author": commit.get("author", "Unknown"),
            })

    return JSONResponse({
        "success": True,
        "project_id": project_id,
        "recent_work": recent_work,
        "features": features,
        "security": security,
        "refactors": refactors,
        "commits": commits,
        "all_events": all_events,
        "total_events": len(all_events),
        "ai_summary": memory.get("ai_summary", ""),
        "active_areas": memory.get("active_areas", []),
        "development_phase": memory.get("development_phase", "active_development"),
        "last_focus": memory.get("last_focus", ""),
        "has_git_history": memory.get("has_git_history", False),
        "total_commits_analyzed": memory.get("total_commits_analyzed", 0),
        "last_active_file": memory.get("last_active_file", ""),
        "total_files": memory.get("total_files", 0),
        "mode": memory.get("mode", "deterministic"),
        # ✅ NEW sections for the memory page UI
        "area_map": area_map,
        "active_files": active_files,
        "stats": {
            "total_functions": len(features),
            "total_routes": len([e for e in features if "endpoint" in e.get("description", "").lower() or "GET" in e.get("title", "") or "POST" in e.get("title", "")]),
            "total_security_areas": len(security),
            "total_refactor_candidates": len(refactors),
            "has_git": memory.get("has_git_history", False),
            "total_commits": memory.get("total_commits_analyzed", 0),
        },
    })