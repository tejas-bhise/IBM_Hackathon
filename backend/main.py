from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from db.mongo import connect_mongo, disconnect_mongo
from services.embedder import get_embedding_model
from routes import upload, analysis, chat, status, mock, summary, workflow, debug, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    get_embedding_model()
    yield
    await disconnect_mongo()


app = FastAPI(
    title="AI Project Intelligence Platform",
    description="Turn any codebase into a living, intelligent system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router,   prefix="/api", tags=["Upload"])
app.include_router(status.router,   prefix="/api", tags=["Status"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(chat.router,     prefix="/api", tags=["Chat"])
app.include_router(summary.router,  prefix="/api", tags=["Summary"])
app.include_router(mock.router,     prefix="/api", tags=["Mock Data"])
app.include_router(workflow.router, prefix="/api", tags=["Workflow"])
app.include_router(memory.router,   prefix="/api", tags=["Memory"])
app.include_router(debug.router,    prefix="/api", tags=["Debug"])


@app.get("/")
async def root():
    return {"status": "API RUNNING", "message": "AI Project Intelligence Platform"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "AI Project Intelligence Platform running"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )