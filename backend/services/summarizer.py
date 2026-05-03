"""
Summarizer — 100% deterministic. Zero LLM calls.
AST/regex rules extract project type, modules, endpoints, and architecture.
"""
import re
import logging

logger = logging.getLogger(__name__)

SKIP_PREFIXES = (
    "docs/", "venv/", ".git/", "__pycache__/", "node_modules/",
    ".mypy_cache/", ".pytest_cache/", "dist/", "build/",
)

PRIORITY_EXT = {".py", ".js", ".ts", ".go", ".java", ".rb", ".rs",
                ".cs", ".jsx", ".tsx", ".vue", ".php"}

FRAMEWORK_PATTERNS = {
    "FastAPI":          re.compile(r"from fastapi|import fastapi", re.I),
    "Django":           re.compile(r"from django|import django", re.I),
    "Flask":            re.compile(r"from flask|import flask|@app\.route", re.I),
    "Express":          re.compile(r"require\(['\"]express", re.I),
    "React":            re.compile(r"from ['\"]react['\"]|import React", re.I),
    "Next.js":          re.compile(r"from ['\"]next['\"]|next/router|next/navigation", re.I),
    "Vue":              re.compile(r"from ['\"]vue['\"]|createApp\(", re.I),
    "SQLAlchemy":       re.compile(r"from sqlalchemy|import sqlalchemy", re.I),
    "Pydantic":         re.compile(r"from pydantic|BaseModel", re.I),
    "OAuth/JWT":        re.compile(r"oauth|OAuth2|jwt|JWT", re.I),
    "Python":           re.compile(r"\.py$"),
    "TypeScript":       re.compile(r"\.ts$|\.tsx$"),
    "JavaScript":       re.compile(r"\.js$|\.jsx$"),
    "SQLite":           re.compile(r"sqlite|SQLite", re.I),
    "PostgreSQL":       re.compile(r"postgresql|psycopg2|asyncpg", re.I),
    "MongoDB":          re.compile(r"pymongo|motor|MongoClient", re.I),
    "Redis":            re.compile(r"redis|aioredis", re.I),
    "Docker":           re.compile(r"dockerfile|docker-compose", re.I),
    "SentenceTransformers": re.compile(r"sentence.transformers|SentenceTransformer", re.I),
    "Groq":             re.compile(r"from groq|import groq|groq\.chat", re.I),
    "Gemini":           re.compile(r"google\.generativeai|import genai", re.I),
}

PROJECT_TYPE_HINTS = {
    "fastapi":  "FastAPI Backend",
    "django":   "Django Backend",
    "flask":    "Flask Backend",
    "express":  "Node.js Backend",
    "react":    "React Frontend",
    "next":     "Next.js App",
    "next.js":  "Next.js App",
    "vue":      "Vue.js App",
    "angular":  "Angular App",
}

MODULE_PURPOSE_MAP = {
    "routes":      "HTTP routing and endpoint definitions",
    "controllers": "Business logic controllers",
    "api":         "API layer and endpoint definitions",
    "services":    "Core business logic and service implementations",
    "models":      "Data models, schemas, and database entities",
    "schemas":     "Request/response schemas and validation",
    "db":          "Database connection and CRUD helpers",
    "database":    "Database layer and query operations",
    "middleware":  "Request/response middleware and guards",
    "utils":       "Utility functions and shared helpers",
    "helpers":     "Helper functions and shared utilities",
    "config":      "Configuration and environment settings",
    "auth":        "Authentication and authorization logic",
    "tests":       "Test suite",
    "handlers":    "Event and request handlers",
    "workers":     "Background workers and async tasks",
    "core":        "Core application logic",
    "lib":         "Shared library code",
    "src":         "Main source code",
    "root":        "Project root files",
}

ENTRY_POINT_NAMES = [
    "main.py", "app.py", "server.py", "index.py", "manage.py",
    "wsgi.py", "asgi.py", "index.js", "index.ts", "app.js", "server.js",
]

_SKIP_DIRS_PUB = {"venv", ".git", "__pycache__", "node_modules", ".venv", "dist", "build"}
_ENDPOINT_PATTERN = re.compile(
    r"""@(?:app|router|blueprint|bp)\.(get|post|put|delete|patch|head|options)\s*\(""",
    re.IGNORECASE,
)
_PATH_PATTERN = re.compile(
    r"""@(?:app|router|bp|blueprint)\.\w+\s*\(\s*['"]([^'"]+)['"]"""
)


# ── Pure helper functions ──────────────────────────────────────────────────────

def _is_skip(path: str) -> bool:
    return any(path.startswith(p) for p in SKIP_PREFIXES)

def _ext(path: str) -> str:
    return "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""

def _detect_tech_stack(files: list) -> list:
    """Returns List[str] — always strings."""
    detected: set = set()
    for f in files:
        path    = str(f.get("path", f.get("file_path", "")))
        content = str(f.get("content", ""))[:2000]
        for name, pat in FRAMEWORK_PATTERNS.items():
            if pat.search(path) or pat.search(content):
                detected.add(str(name))
    return sorted(detected)

def _detect_modules(files: list) -> list:
    """Groups source files by top-level folder."""
    folder_map: dict = {}
    for f in files:
        path = str(f.get("path", f.get("file_path", "")))
        if _is_skip(path):
            continue
        folder = path.split("/")[0] if "/" in path else "root"
        if folder in _SKIP_DIRS_PUB:
            continue
        folder_map.setdefault(folder, []).append(path)

    modules = []
    for folder, paths in list(folder_map.items())[:8]:
        key_files = sorted(
            [p for p in paths if _ext(p) in PRIORITY_EXT],
            key=lambda p: len(p)
        )[:5]
        purpose  = MODULE_PURPOSE_MAP.get(folder.lower(), f"Module: {folder}")
        deps     = _infer_dependencies(folder, folder_map)
        modules.append({
            "name":             folder,
            "key_files":        key_files,
            "purpose":          purpose,
            "responsibilities": purpose,
            "depends_on":       deps,
        })
    return modules

def _infer_dependencies(folder: str, folder_map: dict) -> str:
    lower    = folder.lower()
    all_keys = list(folder_map.keys())
    deps     = []
    if any(x in lower for x in ("route", "api")):
        deps += [k for k in all_keys if any(x in k.lower() for x in ("service", "model", "db"))]
    if any(x in lower for x in ("service",)):
        deps += [k for k in all_keys if any(x in k.lower() for x in ("model", "db", "util"))]
    return ", ".join(deps[:3]) if deps else ""

def _detect_endpoints(files: list) -> list:
    endpoints = []
    for f in files:
        path = str(f.get("path", f.get("file_path", "")))
        if _is_skip(path):
            continue
        content = str(f.get("content", ""))
        for m_method in _ENDPOINT_PATTERN.finditer(content):
            method = m_method.group(1).upper()
            m_path = _PATH_PATTERN.search(content, max(0, m_method.start() - 5))
            ep_path = m_path.group(1) if m_path else "/"
            endpoints.append({
                "method":  method,
                "path":    ep_path,
                "purpose": f"{method} {ep_path}",
                "file":    path,
            })
        if len(endpoints) >= 30:
            break
    return endpoints

def _find_entry_point(files: list) -> str:
    paths = [str(f.get("path", f.get("file_path", ""))) for f in files]
    for candidate in ENTRY_POINT_NAMES:
        for p in paths:
            if p.endswith(candidate) and not _is_skip(p):
                return p
    for p in paths:
        if "/" not in p and p.endswith(".py"):
            return p
    return next((p for p in paths if not _is_skip(p)), paths[0] if paths else "unknown")

def _detect_architecture(modules: list, tech_stack: list) -> str:
    names = [str(m.get("name", "")).lower() for m in modules]
    stack = [str(t).lower() for t in tech_stack]
    if any("service" in n for n in names) and any("route" in n or "api" in n for n in names):
        return "Service-Oriented (routes → services → data)"
    if "django" in stack:
        return "MVT (Django Model-View-Template)"
    if any("model" in n for n in names) and any("view" in n or "controller" in n for n in names):
        return "MVC"
    return "Layered Monolith"

def _detect_project_type(tech_stack: list) -> str:
    stack_lower = [str(t).lower() for t in tech_stack]
    for hint_key, hint_val in PROJECT_TYPE_HINTS.items():
        if any(hint_key in s for s in stack_lower):
            return hint_val
    return "Backend Application"

def _infer_missing_features(modules: list, endpoints: list) -> list:
    """Deterministic check for commonly missing features."""
    module_names  = {str(m.get("name", "")).lower() for m in modules}
    endpoint_paths = [str(e.get("path", "")).lower() for e in endpoints]
    missing = []
    if not any("auth" in n for n in module_names):
        missing.append("Authentication module not detected")
    if not any("test" in n for n in module_names):
        missing.append("Test suite not found")
    if not any("/health" in p or "/ping" in p for p in endpoint_paths):
        missing.append("Health check endpoint missing")
    if not any("log" in n or "middleware" in n for n in module_names):
        missing.append("Logging/middleware layer not detected")
    return missing

def _infer_security_features(tech_stack: list) -> list:
    features = []
    stack_lower = [str(t).lower() for t in tech_stack]
    if any("oauth" in s or "jwt" in s for s in stack_lower):
        features.append("JWT/OAuth authentication")
    if "redis" in stack_lower:
        features.append("Redis session/cache layer")
    if any("sqlalchemy" in s or "pydantic" in s for s in stack_lower):
        features.append("ORM with schema validation")
    return features


# ── Main entry point ───────────────────────────────────────────────────────────

async def run_summarizer(files: list, project_id: str) -> dict:
    """
    Fully deterministic summarizer. No LLM calls. No tokens spent.
    Returns the same shape as before — all consumers continue to work.
    """
    print(f"🧠 Running deterministic summarizer for {len(files)} files...")

    try:
        tech_stack   = _detect_tech_stack(files)
        modules      = _detect_modules(files)
        endpoints    = _detect_endpoints(files)
        entry        = _find_entry_point(files)
        arch         = _detect_architecture(modules, tech_stack)
        ptype        = _detect_project_type(tech_stack)
        src_files    = [f for f in files if not _is_skip(str(f.get("path", f.get("file_path", ""))))]
        missing      = _infer_missing_features(modules, endpoints)
        sec_features = _infer_security_features(tech_stack)

        description = (
            f"A {ptype} with {len(endpoints)} API endpoint(s) across {len(modules)} module(s). "
            f"Architecture: {arch}. "
            f"Tech stack: {', '.join(tech_stack[:6]) or 'Unknown'}."
        )

        print(
            f"✅ Summarizer [deterministic]: {ptype} | "
            f"{len(modules)} modules | {len(endpoints)} endpoints | "
            f"arch={arch} | src_files={len(src_files)}"
        )

        return {
            "project_type":     ptype,
            "description":      description,
            "tech_stack":       tech_stack,       # List[str]
            "main_modules":     modules,
            "architecture":     arch,
            "architecture_type": arch,
            "data_flow":        "Client → API → Service → Database",
            "api_endpoints":    endpoints[:30],
            "entry_point":      entry,
            "missing_features": missing,
            "security_features": sec_features,
            "ai_priority_fix":  missing[0] if missing else "",
            "mode":             "deterministic",
        }

    except Exception as e:
        logger.error(f"❌ Summarizer failed: {e}")
        import traceback; traceback.print_exc()
        return {
            "project_type":     "Unknown",
            "description":      "Analysis failed.",
            "tech_stack":       [],
            "main_modules":     [],
            "architecture":     "Unknown",
            "architecture_type": "Unknown",
            "data_flow":        "",
            "api_endpoints":    [],
            "entry_point":      "unknown",
            "missing_features": [],
            "security_features": [],
            "ai_priority_fix":  "",
            "mode":             "error",
        }


# ── Public stable API (backward-compat exports for tests) ─────────────────────

def detect_stack(files: list) -> list:
    return _detect_tech_stack(files)

def extract_modules_from_files(files: list) -> list:
    return _detect_modules(files)

def extract_endpoints_from_files(files: list) -> list:
    return _detect_endpoints(files)

def detect_entry_point(files: list) -> str:
    return _find_entry_point(files)

def fallback_summary(files: list) -> dict:
    import asyncio
    if not files:
        return {
            "project_type": "Unknown", "description": "No files provided.",
            "entry_point": "Unknown", "main_modules": [], "tech_stack": ["Unknown"],
            "api_endpoints": [], "data_flow": "", "complexity": "UNKNOWN",
            "architecture": "Unknown", "missing_features": [],
        }
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(run_summarizer(files, ""))
    loop.close()
    result["complexity"] = "HIGH" if len(result.get("main_modules", [])) > 6 else "MEDIUM"
    return result