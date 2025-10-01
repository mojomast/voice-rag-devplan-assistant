"""Project management API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.planning import (
    ConversationSummary,
    PlanSummary,
    ProjectCreate,
    ProjectSummary,
    ProjectUpdate,
)
from ..auto_indexer import get_auto_indexer
from ..storage.conversation_store import ConversationStore
from ..storage.plan_store import DevPlanStore
from ..storage.project_store import ProjectStore

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
):
    store = ProjectStore(session)
    project = await store.create_project(
        name=payload.name,
        description=payload.description or "",
        status=payload.status,
        tags=payload.tags,
        repository_path=payload.repository_path,
    )
    try:
        await get_auto_indexer().on_project_created(project)
    except Exception as exc:  # pragma: no cover - best effort indexing
        logger.warning("Project indexing failed: %s", exc)
    return ProjectSummary.from_orm(project)


@router.get("/", response_model=List[ProjectSummary])
async def list_projects(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    tags: Optional[str] = Query(default=None, description="Comma separated tag filter"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    store = ProjectStore(session)
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None
    projects = await store.list_projects(
        status=status_filter,
        search=search,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )
    return [ProjectSummary.from_orm(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    store = ProjectStore(session)
    project = await store.get_project_with_stats(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectSummary.from_orm(project)


@router.put("/{project_id}", response_model=ProjectSummary)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
):
    store = ProjectStore(session)
    project = await store.update_project(
        project_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        tags=payload.tags,
        repository_path=payload.repository_path,
    )
    try:
        await get_auto_indexer().on_project_updated(project)
    except Exception as exc:  # pragma: no cover
        logger.warning("Project re-index failed: %s", exc)
    return ProjectSummary.from_orm(project)


@router.delete("/{project_id}", response_model=ProjectSummary)
async def archive_project(project_id: str, session: AsyncSession = Depends(get_session)):
    store = ProjectStore(session)
    project = await store.archive_project(project_id)
    try:
        await get_auto_indexer().on_project_updated(project)
    except Exception as exc:  # pragma: no cover
        logger.warning("Project archive re-index failed: %s", exc)
    return ProjectSummary.from_orm(project)


@router.get("/{project_id}/plans", response_model=List[PlanSummary])
async def get_project_plans(project_id: str, session: AsyncSession = Depends(get_session)):
    plan_store = DevPlanStore(session)
    plans = await plan_store.list_plans(project_id=project_id)
    return [PlanSummary.from_orm(plan) for plan in plans]


@router.get("/{project_id}/conversations", response_model=List[ConversationSummary])
async def get_project_conversations(project_id: str, session: AsyncSession = Depends(get_session)):
    conversation_store = ConversationStore(session)
    sessions = await conversation_store.list_sessions(project_id=project_id)
    return [ConversationSummary.from_orm(item) for item in sessions]
