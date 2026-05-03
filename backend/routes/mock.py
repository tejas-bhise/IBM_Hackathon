from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import db.mongo as mongo_db

router = APIRouter()

@router.get("/mock/{project_id}")
async def get_mock_data(project_id: str):
    mock = await mongo_db.mock_data_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )
    if not mock:
        raise HTTPException(status_code=404, detail="Mock data not found for this project")
    return JSONResponse({"success": True, **mock})