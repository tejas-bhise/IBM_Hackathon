import asyncio
import re
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from services.ingestion import ingest_github, ingest_zip, generate_project_id
from services.pipeline import run_full_pipeline
import db.mongo as mongo_db

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_ZIP_SIZE_MB = 50
MAX_ZIP_SIZE_BYTES = MAX_ZIP_SIZE_MB * 1024 * 1024

GITHUB_REPO_PATTERN = re.compile(
    r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
)

@router.post("/upload")
async def upload_project(
    file: Optional[UploadFile] = File(None),
    github_url: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    print(f"DEBUG github_url: {github_url}")

    if not file and not github_url:
        raise HTTPException(
            status_code=400,
            detail="Provide either a GitHub repository URL or a ZIP file."
        )

    if file and github_url:
        raise HTTPException(
            status_code=400,
            detail="Provide only one source: either a ZIP file or a GitHub URL, not both."
        )

    project_id = generate_project_id()

    if github_url:
        github_url = github_url.strip()

        if not github_url.startswith("https://github.com/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub URL. Must start with https://github.com/"
            )

        if github_url.endswith(".git"):
            github_url = github_url[:-4]

        clean_url = github_url.rstrip("/")
        parts = clean_url.replace("https://github.com/", "").split("/")

        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid GitHub URL. Must be a repository URL, not a profile URL. "
                    f"Expected: https://github.com/username/repo-name  —  Got: {github_url}"
                )
            )

        if not GITHUB_REPO_PATTERN.match(clean_url + "/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub URL format. Expected: https://github.com/owner/repo-name"
            )

    if file:
        if not file.filename:
            raise HTTPException(status_code=400, detail="ZIP file must have a filename.")

        if not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected .zip, got: {file.filename}"
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_ZIP_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"ZIP file too large. Maximum size: {MAX_ZIP_SIZE_MB}MB, "
                    f"got: {file_size / (1024 * 1024):.1f}MB"
                )
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="ZIP file is empty.")

    await mongo_db.projects_col.insert_one({
        "project_id": project_id,
        "status": "ingesting",
        "pipeline_step": 0,
        "total_steps": 7,
        "percent": 0,
        "current_step_name": "Ingesting repository",
        "source": "github" if github_url else "zip",
        "created_at": datetime.utcnow().isoformat()
    })

    try:
        if github_url:
            logger.info(f"[Upload] Ingesting GitHub repo: {github_url}")
            ingestion = await ingest_github(github_url, project_id)
        elif file:  # ✅ FIX: Explicit check ensures 'file' is not None for Pyright
            logger.info(f"[Upload] Ingesting ZIP file: {file.filename}")
            zip_bytes = await file.read()
            safe_filename: str = file.filename or "upload.zip"
            ingestion = await ingest_zip(zip_bytes, safe_filename, project_id)
        else:
            # Fallback for type consistency
            raise ValueError("No valid input source provided.")

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"[Upload] Validation error for {project_id}: {error_msg}")
        await mongo_db.projects_col.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "error",
                "error": error_msg,
                "error_type": "validation_error"
            }}
        )
        raise HTTPException(status_code=400, detail=error_msg)

    except PermissionError as e:
        error_msg = f"Repository is private or inaccessible: {str(e)}"
        logger.warning(f"[Upload] Permission error for {project_id}: {error_msg}")
        await mongo_db.projects_col.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "error",
                "error": error_msg,
                "error_type": "permission_error"
            }}
        )
        raise HTTPException(
            status_code=403,
            detail="Repository is private or requires authentication. Please use a public repository."
        )

    except TimeoutError as e:
        error_msg = f"Request timed out: {str(e)}"
        logger.error(f"[Upload] Timeout for {project_id}: {error_msg}")
        await mongo_db.projects_col.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "error",
                "error": error_msg,
                "error_type": "timeout_error"
            }}
        )
        raise HTTPException(
            status_code=504,
            detail="Request timed out. Repository may be too large or network is slow."
        )

    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.error(f"[Upload] Unexpected error for {project_id}: {error_msg}", exc_info=True)
        await mongo_db.projects_col.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "error",
                "error": error_msg,
                "error_type": "internal_error"
            }}
        )
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

    files = ingestion["files"]
    project_name = ingestion["project_name"]
    temp_dir = ingestion["temp_dir"]

    if not files:
        error_msg = "No supported code files found in the repository"
        logger.warning(f"[Upload] Empty repo for {project_id}")
        await mongo_db.projects_col.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "error",
                "error": error_msg,
                "error_type": "empty_repository"
            }}
        )
        raise HTTPException(status_code=400, detail=error_msg)

    logger.info(f"[Upload] Starting pipeline for {project_id}: {project_name} ({len(files)} files)")
    asyncio.create_task(
        run_full_pipeline(project_id, files, temp_dir, project_name)
    )

    return JSONResponse({
        "success": True,
        "project_id": project_id,
        "message": f"Analysis started for '{project_name}' ({len(files)} files)",
        "total_files": len(files),
        "project_name": project_name
    })