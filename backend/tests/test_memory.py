"""
Tests for services/memory.py
Covers: infer_feature(), build_deterministic_memory(),
        _categorize_commits(), _parse_git_log().
All deterministic — no LLM, no subprocess needed.
"""
import pytest
from services.memory import (
    infer_feature, build_deterministic_memory,
    _categorize_commits, _parse_git_log, FEATURE_KEYWORDS,
)


# ── infer_feature ──────────────────────────────────────────────────────────────

class TestInferFeature:
    @pytest.mark.parametrize("path,expected", [
        # authentication — checked first
        ("auth.py",              "authentication"),
        ("routes/login.py",      "authentication"),
        ("middleware/jwt.py",    "authentication"),
        # API routing — no auth keyword
        ("routes/api.py",        "API routing"),
        ("routes/router.py",     "API routing"),
        # database — no auth/route keyword
        ("db/mongo.py",          "database layer"),
        ("models/schema.py",     "database layer"),
        # business logic — "service"/"engine"/"handler" in path
        ("engine.py",            "business logic"),
        ("logic/handler.py",     "business logic"),
        # test coverage — no earlier keywords
        ("tests/test_scanner.py","test coverage"),
        ("spec/user.spec.js",    "test coverage"),   # no "auth" in path
        # configuration
        ("config.py",            "configuration"),
        ("settings/env.py",      "configuration"),
        # utilities
        ("utils/helpers.py",     "utilities"),
        ("common/utils.py",      "utilities"),
        # middleware
        ("middleware/cors.py",   "middleware"),
        # file handling — no "handler" (→ business logic) in path
        ("upload.py",            "file handling"),
        ("storage/files.py",     "file handling"),
        # security scanning — no "service" prefix
        ("scanner.py",           "security scanning"),
        ("security/audit.py",    "security scanning"),
        # AI/RAG — no earlier keywords, no "service" prefix
        ("embedder.py",          "AI/RAG pipeline"),
        ("rag/chunks.py",        "AI/RAG pipeline"),
        # code summarization — no earlier keywords, no "service" prefix
        ("summarizer.py",        "code summarization"),
        # project memory — no earlier keywords
        ("memory.py",            "project memory"),
        ("history/tracker.py",   "project memory"),
        # workflow engine
        ("workflow.py",          "workflow engine"),
        ("pipeline/stage.py",    "workflow engine"),
        # core logic — no keyword match
        ("main.py",              "core logic"),
        ("app.py",               "core logic"),
    ])
    def test_path_classification(self, path, expected):
        assert infer_feature(path) == expected, f"Failed for path: {path}"

    def test_returns_string(self):
        assert isinstance(infer_feature("anything.py"), str)

    def test_unknown_path_returns_core_logic(self):
        assert infer_feature("foobar_xyz.py") == "core logic"

    def test_case_insensitive(self):
        assert infer_feature("ROUTES/Auth.PY") == "authentication"


# ── build_deterministic_memory ─────────────────────────────────────────────────

class TestBuildDeterministicMemory:
    def _file(self, path):
        return {"path": path, "content": "", "extension": ".py"}

    def test_returns_dict(self):
        files = [self._file("main.py")]
        result = build_deterministic_memory(files)
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        files = [self._file("routes/api.py"), self._file("services/scanner.py")]
        result = build_deterministic_memory(files)
        for key in ("ai_summary", "recent_work", "active_areas",
                    "development_phase", "last_focus", "change_categories", "mode"):
            assert key in result, f"Missing key: {key}"

    def test_ai_summary_mentions_file_count(self):
        files = [self._file(f"file{i}.py") for i in range(5)]
        result = build_deterministic_memory(files)
        assert "5" in result["ai_summary"]

    def test_mode_is_fallback(self):
        result = build_deterministic_memory([self._file("main.py")])
        assert result["mode"] == "fallback"

    def test_development_phase_is_active(self):
        result = build_deterministic_memory([self._file("main.py")])
        assert result["development_phase"] == "active_development"

    def test_recent_work_is_list(self):
        files = [self._file("routes/api.py"), self._file("services/scanner.py")]
        result = build_deterministic_memory(files)
        assert isinstance(result["recent_work"], list)

    def test_active_areas_is_list(self):
        files = [self._file("routes/api.py"), self._file("services/scanner.py")]
        result = build_deterministic_memory(files)
        assert isinstance(result["active_areas"], list)

    def test_skips_venv_git_pycache(self):
        files = [
            self._file("venv/lib/site.py"),
            self._file(".git/config"),
            self._file("__pycache__/main.pyc"),
            self._file("routes/api.py"),
        ]
        result = build_deterministic_memory(files)
        # active_areas should not include excluded dirs
        for excluded in ("venv", ".git", "__pycache__"):
            assert excluded not in result["active_areas"]

    def test_empty_files_returns_valid_dict(self):
        result = build_deterministic_memory([])
        assert isinstance(result, dict)
        assert result["mode"] == "fallback"

    def test_last_focus_inferred_from_first_file(self):
        files = [self._file("routes/auth.py"), self._file("services/scanner.py")]
        result = build_deterministic_memory(files)
        # First file is routes/auth.py → infer_feature → "authentication"
        assert result["last_focus"] == "authentication"

    def test_recent_work_max_8(self):
        files = [self._file(f"routes/ep{i}.py") for i in range(20)]
        result = build_deterministic_memory(files)
        assert len(result["recent_work"]) <= 8

    def test_active_areas_max_5(self):
        files = [self._file(f"folder{i}/file.py") for i in range(10)]
        result = build_deterministic_memory(files)
        assert len(result["active_areas"]) <= 5


# ── _categorize_commits ────────────────────────────────────────────────────────

class TestCategorizeCommits:
    def _commit(self, message):
        return {"hash": "abcd1234", "message": message,
                "timestamp": "2024-01-01", "author": "Alice"}

    def test_returns_dict(self):
        result = _categorize_commits([])
        assert isinstance(result, dict)

    def test_empty_commits(self):
        assert _categorize_commits([]) == {}

    def test_auth_keyword_matched(self):
        commits = [self._commit("Add JWT token validation")]
        result = _categorize_commits(commits)
        # FEATURE_KEYWORDS is a set — iteration order is nondeterministic.
        # "jwt" and "token" are both keywords in the message; either may win.
        total_entries = sum(len(v) for v in result.values())
        assert total_entries == 1
        assert any(kw in result for kw in ("jwt", "token"))

    def test_fix_keyword_matched(self):
        commits = [self._commit("fix: null pointer in scanner")]
        result = _categorize_commits(commits)
        assert "fix" in result

    def test_each_commit_categorized_once(self):
        # A commit matching multiple keywords is only bucketed under the FIRST match
        commits = [self._commit("fix auth login bug")]
        result = _categorize_commits(commits)
        total_entries = sum(len(v) for v in result.values())
        assert total_entries == 1

    def test_multiple_commits_same_keyword(self):
        # Use messages where only "login" matches (no other FEATURE_KEYWORDS present)
        commits = [
            self._commit("add login feature"),
            self._commit("update login validation"),
        ]
        result = _categorize_commits(commits)
        assert "login" in result
        assert len(result["login"]) == 2

    def test_unrelated_commit_not_categorized(self):
        commits = [self._commit("initial commit with no keywords here xyz")]
        result = _categorize_commits(commits)
        # None of FEATURE_KEYWORDS present → empty dict
        assert result == {}

    def test_all_feature_keywords_in_set(self):
        # Sanity: check a few expected keywords exist
        assert "auth"     in FEATURE_KEYWORDS
        assert "fix"      in FEATURE_KEYWORDS
        assert "upload"   in FEATURE_KEYWORDS
        assert "deploy"   in FEATURE_KEYWORDS


# ── _parse_git_log ─────────────────────────────────────────────────────────────

class TestParseGitLog:
    def test_returns_list_on_nonexistent_path(self, tmp_path):
        result = _parse_git_log(str(tmp_path / "not_a_git_repo"))
        assert isinstance(result, list)
        assert result == []

    def test_returns_list_on_non_git_dir(self, tmp_path):
        # tmp_path exists but has no git repo
        result = _parse_git_log(str(tmp_path))
        assert isinstance(result, list)
        assert result == []

    def test_no_exception_raised(self, tmp_path):
        # Should never raise — gracefully returns []
        try:
            _parse_git_log("/absolute/nonexistent/path/xyz")
        except Exception as e:
            pytest.fail(f"_parse_git_log raised unexpectedly: {e}")

    def test_commit_structure_when_valid(self, tmp_path):
        import subprocess
        # Init a real git repo with one commit
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
            capture_output=True,
        )
        (tmp_path / "file.py").write_text("x = 1")
        subprocess.run(
            ["git", "-C", str(tmp_path), "add", "."], capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-m", "initial commit"],
            capture_output=True,
        )

        result = _parse_git_log(str(tmp_path))
        if result:  # git may not be available in CI
            commit = result[0]
            for key in ("hash", "message", "timestamp", "author"):
                assert key in commit
            assert len(commit["hash"]) == 8
