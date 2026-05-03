from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class RoleEnum(str, Enum):
    dev      = "dev"
    pm       = "pm"
    sales    = "sales"
    investor = "investor"   # ✅ added — test_system.py sends this role


class UploadRequest(BaseModel):
    github_url: Optional[str] = None


class ChatRequest(BaseModel):
    project_id: str
    question:   str
    role:       RoleEnum = RoleEnum.dev


class StatusResponse(BaseModel):
    project_id:    str
    status:        str
    pipeline_step: int
    percent:       int
    error:         Optional[str] = None


class UploadResponse(BaseModel):
    success:    bool
    project_id: str
    message:    str


class AnalysisResponse(BaseModel):
    success:        bool
    project_id:     str
    project_type:   Optional[str]       = None
    description:    Optional[str]       = None
    security_score: Optional[int]       = None
    grade:          Optional[str]       = None
    tech_stack:     Optional[List[str]] = []
    main_modules:   Optional[List[dict]]= []
    data_flow:      Optional[str]       = None
    security_issues:Optional[List[dict]]= []
    memory_summary: Optional[str]       = None
    recent_commits: Optional[List[dict]]= []
    total_issues:   Optional[int]       = 0
    critical_count: Optional[int]       = 0
    high_count:     Optional[int]       = 0
    medium_count:   Optional[int]       = 0
    low_count:      Optional[int]       = 0