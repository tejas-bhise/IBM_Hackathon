import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI:    str = os.getenv("MONGO_URI",    "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "ai_platform")

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL:   str = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")

    # Gemini — no "models/" prefix, new google-genai SDK uses bare name
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL:   str = os.getenv("GEMINI_MODEL",   "gemini-2.0-flash")

    class Config:
        env_file = ".env"
        extra    = "ignore"   # ignore unknown .env keys silently


@lru_cache()
def get_settings() -> Settings:
    return Settings()