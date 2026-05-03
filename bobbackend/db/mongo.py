import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Error 1 fix: use Optional so None is a valid initial value ────────────────
client: Optional[AsyncIOMotorClient] = None
db:     Optional[AsyncIOMotorDatabase] = None

projects_col:          Optional[AsyncIOMotorCollection] = None
security_issues_col:   Optional[AsyncIOMotorCollection] = None
project_summaries_col: Optional[AsyncIOMotorCollection] = None
project_memory_col:    Optional[AsyncIOMotorCollection] = None
embeddings_col:        Optional[AsyncIOMotorCollection] = None
chat_history_col:      Optional[AsyncIOMotorCollection] = None
mock_data_col:         Optional[AsyncIOMotorCollection] = None
code_graph_col:        Optional[AsyncIOMotorCollection] = None
code_structure_col:    Optional[AsyncIOMotorCollection] = None   # ✅ NEW


async def connect_mongo():
    global client, db
    global projects_col, security_issues_col, project_summaries_col
    global project_memory_col, embeddings_col, chat_history_col, mock_data_col
    global code_graph_col, code_structure_col   # ✅ NEW

    client = AsyncIOMotorClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=30000,
    )

    await client.admin.command("ping")
    logger.info("✅ Connected to MongoDB Atlas")

    db = client[settings.MONGO_DB_NAME]

    projects_col          = db["projects"]
    security_issues_col   = db["security_issues"]
    project_summaries_col = db["project_summaries"]
    project_memory_col    = db["project_memory"]
    embeddings_col        = db["embeddings"]
    chat_history_col      = db["chat_history"]
    mock_data_col         = db["mock_data"]
    code_graph_col        = db["code_graph"]
    code_structure_col    = db["code_structure"]   # ✅ NEW

    # Core indexes
    await projects_col.create_index("_id")
    await security_issues_col.create_index("project_id")
    await security_issues_col.create_index([("project_id", 1), ("severity_rank", 1)])
    await project_summaries_col.create_index("project_id")
    await project_memory_col.create_index("project_id")
    await embeddings_col.create_index("project_id")
    await embeddings_col.create_index("chunk_id")
    await chat_history_col.create_index("project_id")
    await chat_history_col.create_index([("project_id", 1), ("created_at", -1)])
    await chat_history_col.create_index(
        "created_at", expireAfterSeconds=86400
    )
    await mock_data_col.create_index("project_id")

    # Code graph indexes
    await code_graph_col.create_index("project_id")
    await code_graph_col.create_index([("project_id", 1), ("file", 1)])

    # ✅ Code structure indexes
    await code_structure_col.create_index("project_id")

    logger.info("✅ All MongoDB indexes ready")


async def disconnect_mongo():
    global client
    if client:
        client.close()
        logger.info("🔌 MongoDB disconnected")


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("DB not connected")
    return db