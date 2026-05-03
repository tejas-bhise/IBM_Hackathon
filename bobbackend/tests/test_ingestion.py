"""
Tests for services/ingestion.py
Covers: generate_project_id(), _walk_and_filter(), cleanup_temp(),
        ingest_zip() validation, ingest_github() URL validation.
Uses real temp filesystem — no mocks needed for pure logic.
"""
import os
import io
import zipfile
import shutil
import tempfile
import pytest
import pytest_asyncio

from services.ingestion import (
    generate_project_id, get_temp_dir, _walk_and_filter,
    cleanup_temp, ingest_zip, ingest_github,
    EXCLUDED_DIRS, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES,
)


# ── generate_project_id ────────────────────────────────────────────────────────

class TestGenerateProjectId:
    def test_length_is_8(self):
        pid = generate_project_id()
        assert len(pid) == 8

    def test_returns_string(self):
        assert isinstance(generate_project_id(), str)

    def test_unique_on_each_call(self):
        ids = {generate_project_id() for _ in range(50)}
        assert len(ids) == 50  # all unique

    def test_alphanumeric_only(self):
        pid = generate_project_id()
        # UUID4 hex is alphanumeric + dashes; first 8 chars are hex digits
        assert all(c in "0123456789abcdef-" for c in pid)


# ── _walk_and_filter ───────────────────────────────────────────────────────────

@pytest.fixture
def temp_project(tmp_path):
    """Create a minimal fake project directory structure."""
    # Allowed files
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.js").write_text("console.log('hi')")
    (tmp_path / "config.yaml").write_text("key: value")
    (tmp_path / "README.md").write_text("# Project")

    # Sub-directory
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "api.py").write_text("from fastapi import APIRouter")

    # Excluded dirs
    for excl in ("node_modules", ".git", "__pycache__", "venv", "dist"):
        d = tmp_path / excl
        d.mkdir()
        (d / "junk.py").write_text("junk")

    # File with excluded extension
    (tmp_path / "image.png").write_bytes(b"\x89PNG")

    # Large file (>300KB)
    (tmp_path / "large.py").write_bytes(b"x" * (MAX_FILE_SIZE_BYTES + 1))

    # Binary file disguised as .txt (null byte)
    (tmp_path / "binary.txt").write_bytes(b"hello\x00world")

    return tmp_path


class TestWalkAndFilter:
    def test_returns_list(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        assert isinstance(result, list)

    def test_allowed_files_included(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        # These should be in results
        assert any("main.py"   in p for p in paths)
        assert any("utils.js"  in p for p in paths)
        assert any("config.yaml" in p for p in paths)

    def test_excluded_dirs_not_included(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        for excl in EXCLUDED_DIRS:
            # exact match on the first path segment — avoid substring false positives
            # (e.g. "out" is a substring of "routes")
            assert not any(p.split(os.sep)[0] == excl for p in paths), \
                f"Excluded dir '{excl}' found in results"

    def test_disallowed_extension_skipped(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        assert not any("image.png" in p for p in paths)

    def test_large_file_skipped(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        assert not any("large.py" in p for p in paths)

    def test_binary_file_skipped(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        assert not any("binary.txt" in p for p in paths)

    def test_file_dict_has_required_keys(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        assert len(result) > 0
        for f in result:
            for key in ("path", "content", "extension", "size_bytes"):
                assert key in f, f"Missing key: {key}"

    def test_content_is_string(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        for f in result:
            assert isinstance(f["content"], str)

    def test_extension_is_lowercase(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        for f in result:
            assert f["extension"] == f["extension"].lower()

    def test_max_150_files_enforced(self, tmp_path):
        # Create 200 small .py files
        for i in range(200):
            (tmp_path / f"file_{i}.py").write_text(f"x = {i}")
        result = _walk_and_filter(str(tmp_path))
        assert len(result) <= 150

    def test_empty_dir_returns_empty(self, tmp_path):
        result = _walk_and_filter(str(tmp_path))
        assert result == []

    def test_subdirectory_files_included(self, temp_project):
        result = _walk_and_filter(str(temp_project))
        paths = [f["path"] for f in result]
        assert any("api.py" in p for p in paths)


# ── cleanup_temp ───────────────────────────────────────────────────────────────

class TestCleanupTemp:
    def test_deletes_existing_dir(self, tmp_path, monkeypatch):
        pid = "testproj"
        target = tmp_path / pid
        target.mkdir()
        (target / "file.py").write_text("x = 1")

        monkeypatch.setattr(
            "services.ingestion.get_temp_dir",
            lambda project_id: str(tmp_path / project_id)
        )
        cleanup_temp(pid)
        assert not target.exists()

    def test_no_error_on_missing_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "services.ingestion.get_temp_dir",
            lambda project_id: str(tmp_path / "nonexistent_dir")
        )
        # Should not raise
        cleanup_temp("any_id")


# ── ingest_zip ─────────────────────────────────────────────────────────────────

def _make_zip(files: dict) -> bytes:
    """Create an in-memory ZIP from a dict of {filename: content}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


class TestIngestZip:
    @pytest.mark.asyncio
    async def test_valid_zip_returns_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr("services.ingestion.get_temp_dir", lambda pid: str(tmp_path / pid))

        zip_bytes = _make_zip({"main.py": "print('hello')", "utils.py": "x = 1"})
        result = await ingest_zip(zip_bytes, "project.zip", "test_pid")

        assert "files" in result
        assert "project_name" in result
        assert result["project_name"] == "project"
        assert result["total_files"] >= 1

    @pytest.mark.asyncio
    async def test_invalid_zip_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("services.ingestion.get_temp_dir", lambda pid: str(tmp_path / pid))

        with pytest.raises(ValueError, match="not a valid ZIP"):
            await ingest_zip(b"this is not a zip file", "bad.zip", "test_pid2")

    @pytest.mark.asyncio
    async def test_project_name_derived_from_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr("services.ingestion.get_temp_dir", lambda pid: str(tmp_path / pid))

        zip_bytes = _make_zip({"app.py": "x=1"})
        result = await ingest_zip(zip_bytes, "my_project.zip", "test_pid3")
        assert result["project_name"] == "my-project"


# ── ingest_github — URL validation ────────────────────────────────────────────

class TestIngestGithubValidation:
    @pytest.mark.asyncio
    async def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await ingest_github("https://gitlab.com/user/repo", "pid")

    @pytest.mark.asyncio
    async def test_non_github_url_raises(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await ingest_github("http://github.com/user/repo", "pid")  # http not https

    @pytest.mark.asyncio
    async def test_plain_url_raises(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await ingest_github("not-a-url", "pid")
