"""Pydantic schemas for development planning APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(default="active")
    tags: Optional[List[str]] = None
    repository_path: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_path: Optional[str] = None


class ProjectSummary(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    plan_count: int = 0
    conversation_count: int = 0

    class Config:
        orm_mode = True


class PlanBase(BaseModel):
    project_id: str
    title: str
    content: str
    status: Optional[str] = "draft"
    metadata: Optional[dict[str, Any]] = None
    conversation_id: Optional[str] = None
    change_summary: Optional[str] = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    conversation_id: Optional[str] = None


class PlanVersion(BaseModel):
    id: str
    version_number: int
    content: str
    change_summary: Optional[str]
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_dict")
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PlanDetail(BaseModel):
    id: str
    project_id: str
    title: str
    status: str
    current_version: int
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_dict")
    created_at: datetime
    updated_at: datetime
    versions: List[PlanVersion] = Field(default_factory=list)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PlanSummary(BaseModel):
    id: str
    project_id: str
    title: str
    status: str
    current_version: int
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_dict")
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PlanExportResponse(BaseModel):
    plan_id: str
    title: str
    version: int
    format: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionCreateRequest(BaseModel):
    content: str
    change_summary: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    modality: str = "text"


class ChatMessageResponse(BaseModel):
    session_id: str
    response: str
    generated_plan_id: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    project_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    summary: Optional[str]
    generated_plans: List[str] = Field(default_factory=list)

    class Config:
        orm_mode = True


class ConversationDetail(ConversationSummary):
    messages: List[dict[str, Any]]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True