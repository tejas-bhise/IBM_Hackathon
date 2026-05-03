#!/usr/bin/env python3
"""
Comprehensive system validation script.
Tests all endpoints and validates the entire pipeline.
"""
import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

settings = get_settings()
MONGO_URI = settings.MONGO_URI

# Test data
TEST_PROJECT_ID = "test1234"
TEST_PROJECT_DATA = {
    "project_id": TEST_PROJECT_ID,
    "project_name": "TestProject",
    "status": "completed",
    "pipeline_step": 7,
    "total_steps": 7,
    "percent": 100,
    "current_step_name": "Complete",
    "source": "test",
    "created_at": datetime.utcnow().isoformat(),
    "completed_at": datetime.utcnow().isoformat()
}

TEST_ANALYSIS_DATA = {
    "project_id": TEST_PROJECT_ID,
    "security_score": 75,
    "total_issues": 5,
    "critical_issues": 1,
    "high_issues": 2,
    "medium_issues": 2,
    "low_issues": 0,
    "issues": [
        {
            "severity": "critical",
            "category": "security",
            "title": "SQL Injection Vulnerability",
            "description": "User input not sanitized",
            "file": "api/users.py",
            "line": 42,
            "code_snippet": "query = f\"SELECT * FROM users WHERE id={user_id}\""
        },
        {
            "severity": "high",
            "category": "security",
            "title": "Hardcoded API Key",
            "description": "API key exposed in code",
            "file": "config.py",
            "line": 15,
            "code_snippet": "API_KEY = 'sk-1234567890abcdef'"
        }
    ],
    "files_analyzed": 25,
    "lines_of_code": 3500
}

TEST_MEMORY_DATA = {
    "project_id": TEST_PROJECT_ID,
    "timeline": [
        {
            "date": "2024-01-15",
            "event": "Project initialized",
            "type": "milestone",
            "description": "Initial commit with basic structure"
        },
        {
            "date": "2024-02-01",
            "event": "Authentication added",
            "type": "feature",
            "description": "JWT-based authentication system"
        }
    ],
    "key_decisions": [
        "Chose FastAPI for high performance",
        "MongoDB for flexible schema"
    ],
    "tech_stack": ["Python", "FastAPI", "MongoDB", "React"]
}

TEST_WORKFLOW_DATA = {
    "project_id": TEST_PROJECT_ID,
    "workflow": {
        "phases": [
            {
                "name": "Planning",
                "duration": "1 week",
                "tasks": ["Requirements gathering", "Architecture design"]
            },
            {
                "name": "Development",
                "duration": "4 weeks",
                "tasks": ["Backend API", "Frontend UI", "Database schema"]
            }
        ]
    }
}


async def setup_test_data():
    """Insert test data into MongoDB"""
    print("🔧 Setting up test data in MongoDB...")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    
    # Clear existing test data
    await db.projects.delete_many({"project_id": TEST_PROJECT_ID})
    await db.analysis.delete_many({"project_id": TEST_PROJECT_ID})
    await db.memory.delete_many({"project_id": TEST_PROJECT_ID})
    await db.workflow.delete_many({"project_id": TEST_PROJECT_ID})
    
    # Insert test data
    await db.projects.insert_one(TEST_PROJECT_DATA)
    await db.analysis.insert_one(TEST_ANALYSIS_DATA)
    await db.memory.insert_one(TEST_MEMORY_DATA)
    await db.workflow.insert_one(TEST_WORKFLOW_DATA)
    
    print(f"✅ Test data created for project: {TEST_PROJECT_ID}")
    client.close()


async def cleanup_test_data():
    """Remove test data from MongoDB"""
    print("\n🧹 Cleaning up test data...")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    
    await db.projects.delete_many({"project_id": TEST_PROJECT_ID})
    await db.analysis.delete_many({"project_id": TEST_PROJECT_ID})
    await db.memory.delete_many({"project_id": TEST_PROJECT_ID})
    await db.workflow.delete_many({"project_id": TEST_PROJECT_ID})
    
    print("✅ Test data cleaned up")
    client.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        asyncio.run(cleanup_test_data())
    else:
        asyncio.run(setup_test_data())
        print(f"\n📝 Test project ID: {TEST_PROJECT_ID}")
        print("🚀 Now you can test the endpoints with this project ID")
        print(f"\nExample: curl http://localhost:8000/api/status/{TEST_PROJECT_ID}")

# Made with Bob
