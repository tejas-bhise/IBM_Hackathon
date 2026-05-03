from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.ai_client import get_availability_status

router = APIRouter()

@router.get("/llm-status")
async def llm_status():
    """Get LLM availability status"""
    return JSONResponse(get_availability_status())

# Made with Bob
