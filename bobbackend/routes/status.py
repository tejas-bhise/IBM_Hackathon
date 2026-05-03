from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from services.ai_client import get_availability_status
import db.mongo as mongo_db

router = APIRouter()

@router.get("/system-status")
async def system_status():
    status = get_availability_status()
    groq_ok   = status["groq"]["available"]
    gemini_ok = status["gemini"]["available"]
    groq_label = (
        "ONLINE" if groq_ok
        else f"COOLDOWN ({status['groq']['cooldown_remaining_s']}s)"
    )
    gemini_label = (
        "ONLINE" if gemini_ok
        else f"COOLDOWN ({status['gemini']['cooldown_remaining_s']}s)"
    )
    return JSONResponse({
        "ai_available":     status["any_available"],
        "active_model":     status["active_model"],
        "services":         {"groq": groq_label, "gemini": gemini_label},
        "groq_available":   groq_ok,
        "gemini_available": gemini_ok,
    })


# ✅ NEW — pipeline poller route (was missing, caused 404 loop)
@router.get("/status/{project_id}")
async def get_project_status(project_id: str):
    project = await mongo_db.projects_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return JSONResponse({
        "project_id":        project.get("project_id"),
        "status":            project.get("status"),
        "pipeline_step":     project.get("pipeline_step", 0),
        "total_steps":       project.get("total_steps", 9),
        "percent":           project.get("percent", 0),
        "current_step_name": project.get("current_step_name", ""),
        "error":             project.get("error"),
    })