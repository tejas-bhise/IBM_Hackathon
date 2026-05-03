import subprocess
import os
import re
import json
import logging
from datetime import datetime
from services.ai_client import smart_llm_call

logger = logging.getLogger(__name__)

SKIP_PREFIXES = ("docs/", "venv/", ".git/", "__pycache__/", "node_modules/")
PRIORITY_EXT = {".py", ".js", ".ts", ".go", ".java", ".rb", ".rs", ".cs", ".jsx", ".tsx"}

IMPORTANT_PATTERNS = [
    "main", "app", "server", "router", "route", "api",
    "auth", "model", "schema", "service", "engine", "handler",
    "config", "db", "database",
]


def _score_file_importance(path: str) -> int:
    lower = path.lower()
    basename = os.path.basename(lower).replace(".py", "").replace(".js", "").replace(".ts", "")
    score = 0
    for i, pattern in enumerate(IMPORTANT_PATTERNS):
        if pattern in basename:
            score += (len(IMPORTANT_PATTERNS) - i)
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in PRIORITY_EXT:
        score += 5
    if any(path.startswith(p) for p in SKIP_PREFIXES):
        score -= 50
    return score


def infer_feature(path: str) -> str:
    lower = path.lower()
    if any(x in lower for x in ("auth", "login", "oauth", "jwt", "token", "session")):
        return "authentication"
    if any(x in lower for x in ("route", "router", "endpoint", "api")):
        return "API routing"
    if any(x in lower for x in ("db", "database", "mongo", "postgres", "sql", "model", "schema")):
        return "database layer"
    if any(x in lower for x in ("service", "logic", "engine", "handler")):
        return "business logic"
    if any(x in lower for x in ("test", "spec")):
        return "test coverage"
    if any(x in lower for x in ("config", "setting", "env")):
        return "configuration"
    if any(x in lower for x in ("util", "helper", "common")):
        return "utilities"
    if any(x in lower for x in ("middleware", "guard", "interceptor")):
        return "middleware"
    if any(x in lower for x in ("upload", "file", "storage")):
        return "file handling"
    if any(x in lower for x in ("scanner", "security", "audit", "pii")):
        return "security scanning"
    if any(x in lower for x in ("embed", "vector", "rag", "chunk")):
        return "AI/RAG pipeline"
    if any(x in lower for x in ("summarizer", "summarise", "summarize")):
        return "code summarization"
    if any(x in lower for x in ("memory", "history", "tracker")):
        return "project memory"
    if any(x in lower for x in ("workflow", "pipeline", "stage")):
        return "workflow engine"
    return "core logic"


FEATURE_KEYWORDS = {
    "auth", "login", "jwt", "token", "oauth", "session",
    "upload", "file", "storage", "download",
    "api", "route", "endpoint", "router",
    "db", "database", "mongo", "sql", "schema", "model",
    "fix", "bug", "patch", "hotfix",
    "deploy", "release", "build", "ci", "cd",
    "test", "spec", "coverage",
    "refactor", "cleanup", "lint",
    "security", "scanner", "audit",
    "embed", "vector", "rag",
    "workflow", "pipeline",
}


def _categorize_commits(commits: list) -> dict:
    buckets: dict = {}
    for commit in commits:
        msg = commit.get("message", "").lower()
        words = set(msg.replace(":", " ").replace("-", " ").replace("_", " ").split())
        for kw in sorted(FEATURE_KEYWORDS):
            if kw in words or kw in msg:
                buckets.setdefault(kw, []).append(commit)
                break
    return buckets


def _extract_functions_from_file(content: str, path: str) -> list:
    """Extract real function/class/route definitions as structured memory events."""
    events = []
    lines = content.split("\n")
    fname = os.path.basename(path)
    feature = infer_feature(path)
    now = datetime.utcnow().isoformat()

    # Python: def/async def/class
    py_def = re.compile(r'^(async\s+def|def|class)\s+(\w+)\s*[\(:]', re.MULTILINE)
    for match in py_def.finditer(content):
        kind = match.group(1).strip()
        name = match.group(2)
        line_num = content[:match.start()].count("\n") + 1

        if kind == "class":
            title = f"Class `{name}` in {fname}"
            desc = f"Class definition `{name}` found in `{path}` at line {line_num}."
            category = "feature"
        else:
            title = f"Function `{name}()` in {fname}"
            desc = f"{'Async function' if 'async' in kind else 'Function'} `{name}()` in `{path}` (line {line_num}) — {feature}."
            category = "feature"

        events.append({
            "title": title,
            "description": desc,
            "category": category,
            "timestamp": now,
            "file": path,
            "line": line_num,
        })

    # FastAPI/Flask routes
    route_pat = re.compile(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', re.I)
    for match in route_pat.finditer(content):
        method = match.group(1).upper()
        route_path = match.group(2)
        line_num = content[:match.start()].count("\n") + 1
        events.append({
            "title": f"{method} {route_path} in {fname}",
            "description": f"API endpoint `{method} {route_path}` defined in `{path}` at line {line_num}.",
            "category": "feature",
            "timestamp": now,
            "file": path,
            "line": line_num,
        })

    return events


def build_deterministic_memory(files: list) -> dict:
    """Build rich structured memory events from actual code."""
    all_events = []
    security_events = []
    refactor_events = []
    now = datetime.utcnow().isoformat()

    # Score and rank files
    scored = []
    for f in files:
        path = str(f.get("path", f.get("file_path", "")))
        score = _score_file_importance(path)
        scored.append((score, path, f))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Extract code definitions from top 20 important files
    top_files = [(s, p, f) for s, p, f in scored if s > 0][:20]

    for score, path, file_data in top_files:
        content = file_data.get("content", "")
        if not content:
            continue
        events = _extract_functions_from_file(content, path)
        all_events.extend(events[:8])  # max 8 events per file

    # Build security events from scanner-detectable patterns
    for score, path, file_data in top_files:
        content = file_data.get("content", "")
        if not content:
            continue
        fname = os.path.basename(path)
        feature = infer_feature(path)

        if any(x in path.lower() for x in ("security", "auth", "jwt", "token", "password", "hash")):
            security_events.append({
                "title": f"Security layer: {fname}",
                "description": f"`{path}` implements {feature} — review for vulnerabilities.",
                "category": "security",
                "timestamp": now,
                "file": path,
            })

    # Build refactor candidates from large files
    for score, path, file_data in scored:
        content = file_data.get("content", "")
        if not content:
            continue
        line_count = content.count("\n")
        if line_count > 200:
            fname = os.path.basename(path)
            refactor_events.append({
                "title": f"Large file: {fname} ({line_count} lines)",
                "description": f"`{path}` has {line_count} lines — consider splitting into smaller modules.",
                "category": "refactor",
                "timestamp": now,
                "file": path,
            })

    # Group by feature area
    area_map: dict = {}
    for _, path, _ in top_files:
        area = infer_feature(path)
        area_map.setdefault(area, []).append(os.path.basename(path))

    # Active areas
    seen: set = set()
    active: list = []
    for _, path, _ in top_files[:20]:
        folder = path.split("/")[0] if "/" in path else "root"
        if folder not in seen and folder not in ("venv", ".git", "__pycache__", "node_modules", "docs"):
            seen.add(folder)
            active.append(folder)

    last_focus = infer_feature(top_files[0][1]) if top_files else "core logic"
    last_active = top_files[0][1] if top_files else "unknown"

    # Separate into categories
    feature_events = [e for e in all_events if e.get("category") == "feature"][:15]
    recent_work = feature_events[:5]

    return {
        "ai_summary": (
            f"Project has {len(files)} files. "
            f"Key areas: {', '.join(list(area_map.keys())[:4])}. "
            f"Top source files: {', '.join([p for _, p, _ in top_files[:3]])}."
        ),
        "recent_work": recent_work,
        "features": feature_events,
        "security": security_events[:8],
        "refactors": refactor_events[:5],
        "active_areas": active[:6],
        "development_phase": "active_development",
        "last_focus": last_focus,
        "last_active_file": last_active,
        "change_categories": {},
        "mode": "fallback",
        "total_files": len(files),
        "area_map": {k: v[:3] for k, v in area_map.items()},
    }


def _parse_git_log(temp_dir: str) -> list:
    try:
        result = subprocess.run(
            ["git", "-C", temp_dir, "log",
             "--format=%H|||%s|||%ai|||%an", "-n", "20", "--no-merges"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|||" not in line:
                continue
            parts = line.split("|||")
            if len(parts) < 4:
                continue
            commits.append({
                "hash": parts[0][:8],
                "message": parts[1].strip(),
                "timestamp": parts[2].strip(),
                "author": parts[3].strip(),
            })
        return commits
    except Exception as e:
        logger.warning(f"⚠️ Git log failed: {e}")
        return []


def _get_recent_files_by_mtime(temp_dir: str, files: list) -> list:
    file_mtimes = []
    for f in files:
        path = str(f.get("path", f.get("file_path", "")))
        full = os.path.join(temp_dir, path)
        if os.path.exists(full):
            try:
                mtime = os.path.getmtime(full)
                file_mtimes.append({
                    "hash": "no-git",
                    "message": path,
                    "timestamp": datetime.fromtimestamp(mtime).isoformat(),
                    "author": "Unknown",
                })
            except Exception:
                pass
    file_mtimes.sort(key=lambda x: x["timestamp"], reverse=True)
    return file_mtimes[:15]


async def run_memory(temp_dir: str, files: list, project_id: str) -> dict:
    print(f"🧠 Building deterministic project memory for {len(files)} files...")
    base = build_deterministic_memory(files)
    commits = _parse_git_log(temp_dir) if os.path.exists(os.path.join(temp_dir, ".git")) else []
    file_commits = commits if commits else _get_recent_files_by_mtime(temp_dir, files)

    # Build prompt for LLM enrichment
    scored = []
    for f in files:
        path = str(f.get("path", f.get("file_path", "")))
        score = _score_file_importance(path)
        scored.append((score, path))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_paths = [p for s, p in scored if s > 0][:12]

    if commits:
        msgs = [c["message"] for c in commits[:10]]
        prompt = (
            f"Git commits ({len(msgs)}):\n"
            + "\n".join(f"{i+1}. {m}" for i, m in enumerate(msgs))
            + f"\n\nTop source files: {', '.join(top_paths[:6])}\n"
            + "Return ONLY JSON (no markdown):\n"
            + '{"ai_summary":"2 sentences mentioning real file names","recent_work":["change1","change2","change3"],"active_areas":["folder1","folder2"],"development_phase":"active_development","last_focus":"main feature"}'
        )
    else:
        prompt = (
            f"Source files ({len(top_paths)}) ranked by importance:\n"
            + "\n".join(f"- {p}" for p in top_paths)
            + "\nReturn ONLY JSON (no markdown):\n"
            + '{"ai_summary":"2 sentences about what this project builds","recent_work":["feature1","feature2","feature3"],"active_areas":["folder1"],"development_phase":"active_development","last_focus":"main area"}'
        )

    ai_data = None
    model_used = "fallback"
    try:
        raw, model_used = await smart_llm_call(prompt, task="memory", max_tokens=300)
        if raw:
            text = raw
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            s = text.find("{")
            e = text.rfind("}") + 1
            if s != -1 and e > 0:
                ai_data = json.loads(text[s:e])
    except Exception as e:
        logger.warning(f"⚠️ Memory error: {e}")

    # Merge AI insights with deterministic base
    if not ai_data or not ai_data.get("ai_summary"):
        ai_data = {}
        model_used = "fallback"

    # ✅ Always use structured event objects from base — never overwrite with plain strings
    now = datetime.utcnow().isoformat()

    # Convert AI string list to structured events if AI gave us plain strings
    def _ai_strings_to_events(items: list, category: str) -> list:
        result = []
        for item in items:
            if isinstance(item, str) and item.strip():
                result.append({
                    "title": item[:80],
                    "description": item,
                    "category": category,
                    "timestamp": now,
                })
            elif isinstance(item, dict):
                result.append(item)
        return result

    ai_recent_work_events = _ai_strings_to_events(ai_data.get("recent_work", []), "feature")

    # Merge: use AI insights for summary text, use base for structured events
    final_recent_work = ai_recent_work_events if ai_recent_work_events else base["recent_work"]
    if len(final_recent_work) < 3:
        final_recent_work = base["recent_work"]

    work_items = len(final_recent_work)
    security_items = len(base["security"])

    print(
        f"✅ Memory [deterministic]: phase={base['development_phase']} | "
        f"work_items={work_items} | security_items={security_items} | git_commits={len(commits)}"
    )

    return {
        "ai_summary": ai_data.get("ai_summary", base["ai_summary"]),
        "recent_work": final_recent_work,
        "features": base["features"],
        "security": base["security"],
        "refactors": base["refactors"],
        "active_areas": ai_data.get("active_areas", base["active_areas"]),
        "development_phase": ai_data.get("development_phase", "active_development"),
        "last_focus": ai_data.get("last_focus", base["last_focus"]),
        "change_categories": ai_data.get("change_categories", {}),
        "commits": file_commits[:15],
        "total_commits_analyzed": len(file_commits),
        "last_active_file": file_commits[0]["message"] if file_commits else base.get("last_active_file", "Unknown"),
        "has_git_history": bool(commits),
        "mode": model_used,
        "total_files": len(files),
        "area_map": base.get("area_map", {}),
    }