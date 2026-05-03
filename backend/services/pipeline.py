import asyncio
from datetime import datetime
from typing import Optional
from services.ingestion import cleanup_temp
from services.scanner import run_scanner
from services.summarizer import run_summarizer
from services.memory import run_memory
from services.embedder import run_embedder
from services.mock_generator import run_mock_generator
from services.alert_builder import build_alerts
from services.workflow_engine import build_workflow
import db.mongo as mongo_db

TOTAL_STEPS = 9


async def _update_status(project_id: str, step: int, step_name: str, error: Optional[str] = None):
    percent = int((step / TOTAL_STEPS) * 100)
    doc = {
        "status": "error" if error else ("completed" if step == TOTAL_STEPS else "processing"),
        "pipeline_step": step,
        "total_steps": TOTAL_STEPS,
        "percent": percent,
        "current_step_name": step_name,
        "updated_at": datetime.utcnow().isoformat(),
    }
    if error:
        doc["error"] = error
    
    if mongo_db.projects_col is not None:
        await mongo_db.projects_col.update_one({"project_id": project_id}, {"$set": doc})


async def run_full_pipeline(
    project_id: str, files: list, temp_dir: str, project_name: str
):
    print(f"\n🚀 Pipeline started: {project_id} | {project_name} | {len(files)} files")

    try:
        # Step 1 — Security scan
        await _update_status(project_id, 1, "Running security + PII scan")
        security_issues = await run_scanner(files, project_id)

        # Step 2 — Build structured alerts
        await _update_status(project_id, 2, "Building security alerts")
        alert_data = build_alerts(security_issues, project_id, total_files=len(files))

        # Step 3 — Summarizer + Memory in parallel
        await _update_status(project_id, 3, "Analyzing codebase structure + history")
        summary_result, memory_result = await asyncio.gather(
            run_summarizer(files, project_id),
            run_memory(temp_dir, files, project_id),
        )

        # Step 4 — Workflow intelligence (rule-based, zero LLM tokens)
        await _update_status(project_id, 4, "Building workflow + role intelligence")
        memory_result["total_files"] = len(files)
        workflow = await build_workflow(alert_data, summary_result, memory_result)

        # Step 5 — Clear OLD results FIRST before embedding
        await _update_status(project_id, 5, "Clearing old results")
        
        delete_tasks = []
        if mongo_db.security_issues_col is not None:
            delete_tasks.append(mongo_db.security_issues_col.delete_many({"project_id": project_id}))
        if mongo_db.project_summaries_col is not None:
            delete_tasks.append(mongo_db.project_summaries_col.delete_many({"project_id": project_id}))
        if mongo_db.project_memory_col is not None:
            delete_tasks.append(mongo_db.project_memory_col.delete_many({"project_id": project_id}))
        if mongo_db.embeddings_col is not None:
            delete_tasks.append(mongo_db.embeddings_col.delete_many({"project_id": project_id}))
        if mongo_db.mock_data_col is not None:
            delete_tasks.append(mongo_db.mock_data_col.delete_many({"project_id": project_id}))
        if mongo_db.code_graph_col is not None:
            delete_tasks.append(mongo_db.code_graph_col.delete_many({"project_id": project_id}))
        
        if delete_tasks:
            await asyncio.gather(*delete_tasks)

        # Step 6 — Embed AFTER clearing
        await _update_status(project_id, 6, "Building semantic search index (RAG)")
        embedded_chunks = await run_embedder(files, project_id)

        code_graph_docs = []
        seen_graph: set = set()
        for chunk in embedded_chunks:
            if chunk["file_path"] not in seen_graph:
                seen_graph.add(chunk["file_path"])
                code_graph_docs.append({
                    "project_id": project_id,
                    "file": chunk["file_path"],
                    "folder": chunk["folder"],
                    "imports": chunk.get("file_imports", []),
                    "functions": chunk.get("file_functions", []),
                    "classes": chunk.get("file_classes", []),
                    "routes": chunk.get("file_routes", []),
                })

        # Step 7 — Mock data generation
        await _update_status(project_id, 7, "Generating synthetic mock data")
        mock_data = await run_mock_generator(security_issues, project_id)

        # Step 8 — Save ALL results atomically
        await _update_status(project_id, 8, "Saving all results to database")
        saves = []

        if alert_data["alerts"] and mongo_db.security_issues_col is not None:
            saves.append(mongo_db.security_issues_col.insert_many(alert_data["alerts"]))

        if mongo_db.project_summaries_col is not None:
            saves.append(mongo_db.project_summaries_col.insert_one({
                "project_id": project_id,
                **summary_result,
                "security_score": alert_data["security_score"],
                "grade": alert_data["grade"],
                "total_issues": alert_data["total_issues"],
                "critical_count": alert_data["critical_count"],
                "high_count": alert_data["high_count"],
                "medium_count": alert_data["medium_count"],
                "low_count": alert_data["low_count"],
                "summary_text": alert_data["summary"],
                "created_at": datetime.utcnow().isoformat(),
            }))

        if mongo_db.project_memory_col is not None:
            saves.append(mongo_db.project_memory_col.insert_one({
                "project_id": project_id,
                **memory_result,
                "created_at": datetime.utcnow().isoformat(),
            }))

        if embedded_chunks and mongo_db.embeddings_col is not None:
            saves.append(mongo_db.embeddings_col.insert_many(embedded_chunks))

        if code_graph_docs and mongo_db.code_graph_col is not None:
            saves.append(mongo_db.code_graph_col.insert_many(code_graph_docs))

        if mongo_db.mock_data_col is not None:
            saves.append(mongo_db.mock_data_col.insert_one({
                "project_id": project_id,
                **mock_data,
                "created_at": datetime.utcnow().isoformat(),
            }))

        if saves:
            await asyncio.gather(*saves)

        # Step 9 — Finalize project document
        if mongo_db.projects_col is not None:
            await mongo_db.projects_col.update_one(
                {"project_id": project_id},
                {"$set": {
                    "status": "completed",
                    "pipeline_step": TOTAL_STEPS,
                    "total_steps": TOTAL_STEPS,
                    "percent": 100,
                    "current_step_name": "Completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "total_files_analyzed": len(files),
                    "project_name": project_name,
                    "workflow": workflow,
                }},
            )

    except Exception as e:
        print(f"❌ Pipeline failed [{project_id}]: {e}")
        import traceback
        traceback.print_exc()
        await _update_status(project_id, 0, "Failed", error=str(e))

    finally:
        cleanup_temp(project_id)