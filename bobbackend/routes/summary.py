from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import db.mongo as mongo_db

router = APIRouter()

@router.get("/summary/{project_id}")
async def get_summary(project_id: str):
    summary = await mongo_db.project_summaries_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this project")
    return JSONResponse({"success": True, **summary})