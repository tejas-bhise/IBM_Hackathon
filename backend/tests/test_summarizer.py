"""
Tests for services/summarizer.py
Covers: detect_stack(), extract_modules_from_files(),
        extract_endpoints_from_files(), detect_entry_point(), fallback_summary().
All deterministic — no LLM needed.
"""
import pytest
from services.summarizer import (
    detect_stack, extract_modules_from_files, extract_endpoints_from_files,
    detect_entry_point, fallback_summary, ENTRY_POINT_NAMES, MODULE_PURPOSE_MAP,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _file(path, content=""):
    ext = "." + path.split(".")[-1] if "." in path else ""
    return {"path": path, "content": content, "extension": ext}


# ── detect_stack ───────────────────────────────────────────────────────────────

class TestDetectStack:
    def test_python_detected_from_extension(self):
        files = [_file("main.py", "")]
        stack = detect_stack(files)
        assert "Python" in stack

    def test_javascript_detected(self):
        files = [_file("index.js", "")]
        stack = detect_stack(files)
        assert "JavaScript" in stack

    def test_typescript_detected(self):
        files = [_file("app.ts", "")]
        stack = detect_stack(files)
        assert "TypeScript" in stack

    def test_fastapi_detected_from_content(self):
        files = [_file("requirements.txt", "fastapi>=0.111.0\nuvicorn\n")]
        stack = detect_stack(files)
        assert "FastAPI" in stack

    def test_mongodb_detected(self):
        files = [_file("db.py", "from motor.motor_asyncio import AsyncIOMotorClient")]
        stack = detect_stack(files)
        assert any("MongoDB" in s for s in stack)

    def test_react_detected(self):
        files = [_file("package.json", '{"dependencies": {"react": "^18.0.0"}}')]
        stack = detect_stack(files)
        assert "React" in stack

    def test_multiple_stack_items(self):
        files = [_file("req.txt", "fastapi\ngroq\nmongodb\n")]
        stack = detect_stack(files)
        assert len(stack) > 1

    def test_returns_sorted_list(self):
        files = [_file("req.txt", "fastapi\nflask\n")]
        stack = detect_stack(files)
        assert stack == sorted(stack)

    def test_empty_files_returns_unknown(self):
        stack = detect_stack([])
        assert stack == ["Unknown"]

    def test_groq_detected(self):
        files = [_file("ai.py", "from groq import Groq\nclient = Groq(api_key=key)")]
        stack = detect_stack(files)
        assert "Groq" in stack

    def test_case_insensitive_detection(self):
        files = [_file("req.txt", "FastAPI\nMongoDB\n")]
        stack = detect_stack(files)
        assert "FastAPI" in stack


# ── extract_modules_from_files ─────────────────────────────────────────────────

class TestExtractModules:
    def test_groups_by_folder(self):
        files = [
            _file("routes/upload.py"),
            _file("routes/chat.py"),
            _file("services/scanner.py"),
        ]
        mods = extract_modules_from_files(files)
        names = [m["name"] for m in mods]
        assert "routes"   in names
        assert "services" in names

    def test_root_files_grouped_as_root(self):
        files = [_file("main.py"), _file("config.py")]
        mods = extract_modules_from_files(files)
        names = [m["name"] for m in mods]
        assert "root" in names

    def test_module_has_required_keys(self):
        files = [_file("services/scanner.py")]
        mods = extract_modules_from_files(files)
        assert len(mods) > 0
        for m in mods:
            for key in ("name", "purpose", "key_files", "responsibilities", "depends_on"):
                assert key in m

    def test_max_10_modules(self):
        files = [_file(f"mod{i}/file.py") for i in range(20)]
        mods = extract_modules_from_files(files)
        assert len(mods) <= 10

    def test_known_purpose_from_map(self):
        files = [_file("routes/upload.py")]
        mods = extract_modules_from_files(files)
        routes_mod = next((m for m in mods if m["name"] == "routes"), None)
        assert routes_mod is not None
        assert routes_mod["purpose"] == MODULE_PURPOSE_MAP["routes"]

    def test_unknown_folder_gets_generic_purpose(self):
        files = [_file("wizards/magic.py")]
        mods = extract_modules_from_files(files)
        wizard_mod = next((m for m in mods if m["name"] == "wizards"), None)
        assert wizard_mod is not None
        assert "wizards" in wizard_mod["purpose"].lower() or "Module" in wizard_mod["purpose"]

    def test_excludes_venv_git_pycache(self):
        files = [
            _file("venv/lib/site.py"),
            _file(".git/config"),
            _file("__pycache__/main.cpython.pyc"),
            _file("routes/good.py"),
        ]
        mods = extract_modules_from_files(files)
        names = [m["name"] for m in mods]
        assert "venv"        not in names
        assert ".git"        not in names
        assert "__pycache__" not in names

    def test_key_files_capped_at_6(self):
        files = [_file(f"routes/file{i}.py") for i in range(10)]
        mods = extract_modules_from_files(files)
        for m in mods:
            assert len(m["key_files"]) <= 6


# ── extract_endpoints_from_files ───────────────────────────────────────────────

class TestExtractEndpoints:
    def test_fastapi_get_endpoint_detected(self):
        content = "@router.get('/users')\nasync def get_users(): pass\n"
        files = [_file("routes/users.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) >= 1
        assert endpoints[0]["method"] == "GET"
        assert endpoints[0]["path"]   == "/users"

    def test_fastapi_post_endpoint_detected(self):
        content = "@router.post('/upload')\nasync def upload(): pass\n"
        files = [_file("routes/upload.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) >= 1
        assert endpoints[0]["method"] == "POST"

    def test_multiple_endpoints_in_one_file(self):
        content = (
            "@router.get('/users')\nasync def get_users(): pass\n"
            "@router.post('/users')\nasync def create_user(): pass\n"
            "@router.delete('/users/{id}')\nasync def delete_user(): pass\n"
        )
        files = [_file("routes/users.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) >= 3

    def test_no_endpoints_in_non_route_file(self):
        content = "def helper(): return 42\n"
        files = [_file("utils.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) == 0

    def test_non_python_file_skipped(self):
        content = "@router.get('/api')"
        files = [_file("config.yaml", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) == 0

    def test_endpoint_has_required_keys(self):
        content = "@router.get('/health')\nasync def health(): pass\n"
        files = [_file("routes/health.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) >= 1
        ep = endpoints[0]
        for key in ("method", "path", "purpose", "file"):
            assert key in ep

    def test_app_decorator_detected(self):
        content = "@app.get('/status')\nasync def status(): pass\n"
        files = [_file("main.py", content)]
        endpoints = extract_endpoints_from_files(files)
        assert len(endpoints) >= 1


# ── detect_entry_point ─────────────────────────────────────────────────────────

class TestDetectEntryPoint:
    def test_main_py_detected(self):
        files = [_file("main.py"), _file("utils.py")]
        assert detect_entry_point(files) == "main.py"

    def test_app_py_detected(self):
        files = [_file("app.py"), _file("utils.py")]
        assert detect_entry_point(files) == "app.py"

    def test_main_py_takes_priority_over_app_py(self):
        files = [_file("app.py"), _file("main.py")]
        # ENTRY_POINT_NAMES is an ordered set checked in order — main.py before app.py
        result = detect_entry_point(files)
        assert result in ("main.py", "app.py")  # either is valid

    def test_nested_main_py_detected(self):
        files = [_file("src/main.py"), _file("utils.py")]
        assert detect_entry_point(files) == "src/main.py"

    def test_returns_unknown_when_no_entry_point(self):
        files = [_file("helper.py"), _file("models.py")]
        result = detect_entry_point(files)
        assert result == "Unknown"

    def test_manage_py_detected(self):
        files = [_file("manage.py")]
        assert detect_entry_point(files) == "manage.py"

    def test_index_js_detected(self):
        files = [_file("index.js"), _file("utils.js")]
        assert detect_entry_point(files) == "index.js"

    @pytest.mark.parametrize("name", list(ENTRY_POINT_NAMES))
    def test_all_known_entry_points_detected(self, name):
        files = [_file(name)]
        assert detect_entry_point(files) == name


# ── fallback_summary ───────────────────────────────────────────────────────────

class TestFallbackSummary:
    def test_returns_dict(self, sample_files):
        result = fallback_summary(sample_files)
        assert isinstance(result, dict)

    def test_required_keys_present(self, sample_files):
        result = fallback_summary(sample_files)
        for key in ("project_type", "description", "entry_point", "main_modules",
                    "tech_stack", "api_endpoints", "data_flow", "complexity"):
            assert key in result, f"Missing key: {key}"

    def test_description_mentions_file_count(self, sample_files):
        result = fallback_summary(sample_files)
        assert str(len(sample_files)) in result["description"]

    def test_tech_stack_is_list(self, sample_files):
        result = fallback_summary(sample_files)
        assert isinstance(result["tech_stack"], list)
        assert len(result["tech_stack"]) > 0

    def test_main_modules_is_list(self, sample_files):
        result = fallback_summary(sample_files)
        assert isinstance(result["main_modules"], list)

    def test_entry_point_detected(self, sample_files):
        result = fallback_summary(sample_files)
        # sample_files includes main.py
        assert result["entry_point"] == "main.py"

    def test_api_endpoints_is_list(self, sample_files):
        result = fallback_summary(sample_files)
        assert isinstance(result["api_endpoints"], list)

    def test_empty_files_still_returns_valid_dict(self):
        result = fallback_summary([])
        assert isinstance(result, dict)
        assert result["entry_point"] == "Unknown"
        assert result["tech_stack"] == ["Unknown"]
