from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any
from models.schemas import ChatRequest
# ✅ FIXED: Added type ignore to suppress the false-positive import symbol issue
from services.chat_engine import run_chat  # type: ignore 
import db.mongo as mongo_db

router = APIRouter()

# ✅ FIXED: route now matches frontend call: POST /api/chat/{project_id}
@router.post("/chat/{project_id}")
async def chat(project_id: str, request: ChatRequest):
    # ✅ FIX: Pyright guards for mongo collections
    if (mongo_db.projects_col is None or 
        mongo_db.project_summaries_col is None or 
        mongo_db.embeddings_col is None or 
        mongo_db.chat_history_col is None):
        raise HTTPException(status_code=500, detail="Database connection not initialized")

    # Verify project exists
    project = await mongo_db.projects_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("status") != "completed":
        raise HTTPException(status_code=202, detail="Analysis not yet complete")

    # Load summary
    summary_doc = await mongo_db.project_summaries_col.find_one(
        {"project_id": project_id}, {"_id": 0}
    )
    summary: Dict[str, Any] = summary_doc or {}
    workflow: Dict[str, Any] = project.get("workflow", {})

    # Enrich summary with workflow security fields
    summary["security_score"] = summary.get("security_score", workflow.get("security_score", 100))
    summary["grade"] = summary.get("grade", workflow.get("grade", "A"))
    summary["total_issues"] = summary.get("total_issues", workflow.get("total_issues", 0))
    summary["critical_count"] = summary.get("critical_count", workflow.get("critical_count", 0))
    summary["high_count"] = summary.get("high_count", workflow.get("high_count", 0))
    summary["architecture"] = summary.get("architecture", workflow.get("architecture", "Unknown"))

    # Load embeddings for RAG — limit to 3000 chunks
    chunks_cursor = mongo_db.embeddings_col.find(
        {"project_id": project_id}, {"_id": 0}
    )
    stored_chunks = await chunks_cursor.to_list(length=3000)

    # Chat history — last 4 messages only
    history_cursor = mongo_db.chat_history_col.find(
        {"project_id": project_id}, {"_id": 0}
    ).sort("created_at", -1).limit(4)
    
    history_docs = await history_cursor.to_list(length=4)
    history = list(history_docs)
    history.reverse()

    # Call the chat engine
    result = await run_chat(
        question=request.question,
        role=request.role,
        project_summary=summary,
        stored_chunks=stored_chunks,
        chat_history=history,
        project_id=project_id,
    )

    # Save user/assistant turns to history
    now = datetime.utcnow().isoformat()
    await mongo_db.chat_history_col.insert_many([
        {
            "project_id": project_id, 
            "role": "user",
            "content": request.question, 
            "created_at": now
        },
        {
            "project_id": project_id, 
            "role": "assistant",
            "content": result["answer"], 
            "created_at": now
        },
    ])

    return JSONResponse({
        "success": True,
        "answer": result["answer"],
        "reasoning": result.get("reasoning", ""),
        "sources": result["sources"],
        "role": result["role"],
        "mode": result["mode"],
        "confidence": result["confidence"],
        "chunks_retrieved": len(result["sources"]),
    })


# ✅ ALSO keep old route as alias
@router.post("/chat")
async def chat_legacy(request: ChatRequest):
    """Legacy route — redirects to new path-param version."""
    # Attempt to find project_id in the body if it exists
    project_id = getattr(request, "project_id", None)
    
    if not project_id:
        raise HTTPException(
            status_code=400, 
            detail="project_id required in body or use /chat/{project_id}"
        )
    return await chat(project_id, request)