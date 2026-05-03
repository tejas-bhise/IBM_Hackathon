import os
import uuid
import zipfile
import shutil
import logging
import time
from pathlib import Path
import git

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rb", ".php", ".env", ".yaml", ".yml", ".json",
    ".toml", ".xml", ".html", ".css", ".md", ".txt", ".sh"
}

EXCLUDED_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    "venv", ".venv", "vendor", ".next", "coverage",
    ".pytest_cache", "target", "out", ".idea", ".vscode"
}

MAX_FILE_SIZE_BYTES = 300 * 1024  # 300KB
MAX_FILE_COUNT = 150
CLONE_TIMEOUT_SECONDS = 180  # ✅ FIXED


def generate_project_id() -> str:
    return str(uuid.uuid4())[:8]


def get_temp_dir(project_id: str) -> str:
    return f"/tmp/{project_id}"


async def ingest_github(github_url: str, project_id: str) -> dict:
    if not github_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Must start with https://github.com/")

    github_url = github_url.rstrip("/")
    if github_url.endswith(".git"):
        github_url = github_url[:-4]

    parts = github_url.replace("https://github.com/", "").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")

    temp_dir = get_temp_dir(project_id)

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

    # ✅ RETRY LOGIC ADDED
    last_error = None

    for attempt in range(2):
        try:
            logger.info(f"[Ingestion] Cloning (attempt {attempt+1}) {github_url}")

            git.Repo.clone_from(
                github_url,
                temp_dir,
                depth=1,                 # ✅ SHALLOW CLONE
                single_branch=True       # ✅ FIXED (removed multi_options)
            )

            break  # success

        except git.GitCommandError as e:
            last_error = e
            logger.warning(f"[Ingestion] Clone failed (attempt {attempt+1}): {str(e)}")

            if attempt == 1:
                error_msg = str(e).lower()

                if "authentication" in error_msg or "permission denied" in error_msg:
                    raise PermissionError("Repository is private or requires authentication")
                elif "not found" in error_msg:
                    raise ValueError("Repository not found. Check URL.")
                elif "timeout" in error_msg:
                    raise TimeoutError("Clone operation timed out.")
                else:
                    raise ValueError(f"Failed to clone repository: {str(e)}")

            time.sleep(2)

        except Exception as e:
            last_error = e
            if attempt == 1:
                raise ValueError(f"Unexpected error during clone: {str(e)}")
            time.sleep(2)

    if not os.path.exists(temp_dir):
        raise ValueError("Clone succeeded but directory not found")

    files = _walk_and_filter(temp_dir)

    if not files:
        cleanup_temp(project_id)
        raise ValueError("Repository contains no supported code files")

    repo_name = github_url.split("/")[-1]

    logger.info(f"[Ingestion] Successfully ingested {len(files)} files from {repo_name}")

    return {
        "files": files,
        "project_name": repo_name,
        "temp_dir": temp_dir,
        "total_files": len(files)
    }


async def ingest_zip(zip_bytes: bytes, filename: str, project_id: str) -> dict:
    if not zip_bytes:
        raise ValueError("ZIP file is empty")

    if len(zip_bytes) > 50 * 1024 * 1024:
        raise ValueError("ZIP file too large (max 50MB)")

    temp_dir = get_temp_dir(project_id)
    zip_path = f"/tmp/{project_id}.zip"

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    os.makedirs(temp_dir, exist_ok=True)

    try:
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Uploaded file is not a valid ZIP archive")

        with zipfile.ZipFile(zip_path, "r") as zf:
            total_size = sum(info.file_size for info in zf.infolist())

            if total_size > 500 * 1024 * 1024:
                raise ValueError("ZIP archive too large when uncompressed")

            if len(zf.infolist()) > 5000:
                raise ValueError("ZIP contains too many files")

            zf.extractall(temp_dir)

    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    if not os.path.exists(temp_dir):
        raise ValueError("Extraction failed")

    files = _walk_and_filter(temp_dir)

    if not files:
        cleanup_temp(project_id)
        raise ValueError("ZIP contains no supported files")

    project_name = filename.replace(".zip", "")

    return {
        "files": files,
        "project_name": project_name,
        "temp_dir": temp_dir,
        "total_files": len(files)
    }


def _walk_and_filter(root_dir: str) -> list:
    all_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = Path(filename).suffix.lower()

            if ext not in ALLOWED_EXTENSIONS:
                continue

            try:
                file_size = os.path.getsize(filepath)
            except:
                continue

            if file_size > MAX_FILE_SIZE_BYTES:
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                continue

            if "\x00" in content[:1000]:
                continue

            relative_path = os.path.relpath(filepath, root_dir)

            all_files.append({
                "path": relative_path,
                "content": content,
                "extension": ext,
                "size_bytes": file_size
            })

    if len(all_files) > MAX_FILE_COUNT:
        all_files.sort(key=lambda x: x["size_bytes"], reverse=True)
        all_files = all_files[:MAX_FILE_COUNT]

    return all_files


def cleanup_temp(project_id: str):
    temp_dir = get_temp_dir(project_id)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)