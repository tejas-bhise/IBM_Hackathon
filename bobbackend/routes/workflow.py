from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import db.mongo as mongo_db

router = APIRouter()

async def _get_project_or_404(project_id: str) -> dict:
    project = await mongo_db.projects_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("status") != "completed":
        raise HTTPException(status_code=202, detail="Analysis not yet complete")
    return project

@router.get("/workflow/{project_id}")
async def get_workflow(project_id: str):
    project = await _get_project_or_404(project_id)
    workflow = project.get("workflow", {})
    return JSONResponse({"success": True, "project_id": project_id, "workflow": workflow})

@router.get("/workflow/{project_id}/view/dev")
async def workflow_dev_view(project_id: str):
    project  = await _get_project_or_404(project_id)
    workflow = project.get("workflow", {})
    dev_view = workflow.get("dev_view", {})
    if not dev_view:
        raise HTTPException(status_code=404, detail="Dev view not found — re-run analysis")
    return JSONResponse({"success": True, "project_id": project_id, "role": "developer", "view": dev_view})

@router.get("/workflow/{project_id}/view/pm")
async def workflow_pm_view(project_id: str):
    project  = await _get_project_or_404(project_id)
    workflow = project.get("workflow", {})
    pm_view  = workflow.get("pm_view", {})
    if not pm_view:
        raise HTTPException(status_code=404, detail="PM view not found — re-run analysis")
    return JSONResponse({"success": True, "project_id": project_id, "role": "pm", "view": pm_view})

@router.get("/workflow/{project_id}/view/investor")
async def workflow_investor_view(project_id: str):
    project       = await _get_project_or_404(project_id)
    workflow      = project.get("workflow", {})
    investor_view = workflow.get("investor_view", {})
    if not investor_view:
        raise HTTPException(status_code=404, detail="Investor view not found — re-run analysis")
    return JSONResponse({"success": True, "project_id": project_id, "role": "investor", "view": investor_view})

@router.get("/workflow/{project_id}/summary")
async def workflow_summary(project_id: str):
    project  = await _get_project_or_404(project_id)
    workflow = project.get("workflow", {})
    return JSONResponse({
        "success":        True,
        "project_id":     project_id,
        "stage":          workflow.get("stage", ""),
        "risk":           workflow.get("risk", ""),
        "action":         workflow.get("action", ""),
        "security_score": workflow.get("security_score", 0),
        "grade":          workflow.get("grade", ""),
        "total_issues":   workflow.get("total_issues", 0),
        "critical_count": workflow.get("critical_count", 0),
        "high_count":     workflow.get("high_count", 0),
        "medium_count":   workflow.get("medium_count", 0),
        "low_count":      workflow.get("low_count", 0),
        "mode":           workflow.get("mode", "rule-based"),
    })