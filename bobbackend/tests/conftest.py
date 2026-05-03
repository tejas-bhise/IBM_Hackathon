# ── Must come first — env vars + sys.modules stubs before any service import ───
import os
import sys
from unittest.mock import MagicMock, AsyncMock

os.environ.setdefault("MONGO_URI",       "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME",   "test_ai_platform")
os.environ.setdefault("GEMINI_API_KEY",  "test-gemini-key-xxxx")
os.environ.setdefault("GROQ_API_KEY",    "test-groq-key-xxxx")
os.environ.setdefault("GROQ_MODEL",      "llama-3.3-70b-versatile")
os.environ.setdefault("GEMINI_MODEL",    "gemini-2.0-flash")

# Stub optional heavy deps that may not be installed in the test environment.
# These must be in sys.modules *before* any service module is imported so that
# top-level "from groq import ..." / "from google import genai" don't fail.
def _make_mock_module(name: str) -> MagicMock:
    mod = MagicMock()
    mod.__name__ = name
    return mod

for _mod in (
    "groq", "groq._client", "groq._async_client",
    "google", "google.genai", "google.genai.types",
    "motor", "motor.motor_asyncio",
    "sentence_transformers",
    "sklearn", "sklearn.metrics", "sklearn.metrics.pairwise",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = _make_mock_module(_mod)

# Make groq.Groq / groq.AsyncGroq importable as classes
sys.modules["groq"].Groq      = MagicMock()
sys.modules["groq"].AsyncGroq = MagicMock()

# Make google.genai.Client importable
sys.modules["google.genai"].Client = MagicMock()
sys.modules["google.genai"].types  = sys.modules["google.genai.types"]

import pytest
from unittest.mock import patch


# ── Patch Groq + Gemini at import time — no real API calls in tests ───────────

@pytest.fixture(autouse=True)
def mock_groq(monkeypatch):
    """Prevent every test from hitting the real Groq API."""
    mock_client   = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"confirmed": true, "severity": "HIGH"}'
    mock_client.chat.completions.create.return_value        = mock_response
    # Also mock async client
    mock_async = MagicMock()
    mock_async.chat.completions.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr("groq.Groq",      lambda **kwargs: mock_client,   raising=False)
    monkeypatch.setattr("groq.AsyncGroq", lambda **kwargs: mock_async,    raising=False)
    return mock_client


@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    """Prevent every test from hitting the real Gemini API."""
    mock_client = MagicMock()
    mock_resp   = MagicMock()
    mock_resp.text = "mock gemini response"
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
    monkeypatch.setattr("google.genai.Client", lambda **kwargs: mock_client, raising=False)
    return mock_client


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_files():
    return [
        {"path": "main.py",             "content": "from fastapi import FastAPI\napp = FastAPI()\n", "extension": ".py", "size_bytes": 100},
        {"path": "routes/upload.py",    "content": "@router.post('/upload')\nasync def upload(): pass\n", "extension": ".py", "size_bytes": 200},
        {"path": "services/scanner.py", "content": "import re\ndef scan(): pass\n", "extension": ".py", "size_bytes": 150},
        {"path": "db/mongo.py",         "content": "from motor.motor_asyncio import AsyncIOMotorClient\n", "extension": ".py", "size_bytes": 80},
        {"path": "models/schemas.py",   "content": "from pydantic import BaseModel\n", "extension": ".py", "size_bytes": 60},
    ]


@pytest.fixture
def confirmed_critical_issue():
    return {
        "confirmed":      True,
        "file_path":      "routes/users.py",
        "line_number":    42,
        "type":           "SQL_INJECTION",
        "severity":       "CRITICAL",
        "matched_text":   "SELECT * FROM users WHERE id = " + "user_id",
        "code_snippet":   "query = 'SELECT * FROM users WHERE id = ' + user_id",
        "explanation":    "User input concatenated into SQL",
        "fix_suggestion": "Use parameterized queries",
        "before_code":    "query = 'SELECT * FROM users WHERE id = ' + user_id",
        "after_code":     "cursor.execute('SELECT * FROM users WHERE id = ?', [user_id])",
    }


@pytest.fixture
def confirmed_high_issue():
    return {
        "confirmed":      True,
        "file_path":      "config.py",
        "line_number":    10,
        "type":           "HARDCODED_PASSWORD",
        "severity":       "HIGH",
        "matched_text":   "password='secret123'",
        "code_snippet":   "db_password = 'secret123'",
        "explanation":    "Hardcoded password",
        "fix_suggestion": "Use environment variable",
        "before_code":    "password = 'secret123'",
        "after_code":     "password = os.environ['DB_PASSWORD']",
    }


@pytest.fixture
def confirmed_medium_issue():
    return {
        "confirmed":      True,
        "file_path":      "api/users.py",
        "line_number":    88,
        "type":           "PII_EMAIL",
        "severity":       "MEDIUM",
        "matched_text":   "admin@example.com",
        "code_snippet":   "ADMIN_EMAIL = 'admin@example.com'",
        "explanation":    "Hardcoded email address",
        "fix_suggestion": "Move to environment variable",
        "before_code":    "",
        "after_code":     "",
    }


@pytest.fixture
def confirmed_low_issue():
    return {
        "confirmed":      True,
        "file_path":      "tests/test_api.py",
        "line_number":    5,
        "type":           "PII_PHONE",
        "severity":       "LOW",
        "matched_text":   "9876543210",
        "code_snippet":   "phone = '9876543210'",
        "explanation":    "Phone number in test file",
        "fix_suggestion": "Use fake test data",
        "before_code":    "",
        "after_code":     "",
    }
