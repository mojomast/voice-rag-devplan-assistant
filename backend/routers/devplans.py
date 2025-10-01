"""Development plan API routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.planning import (
    PlanCreate,
    PlanDetail,
    PlanExportResponse,
    PlanSummary,
    PlanUpdate,
    PlanVersion,
    VersionCreateRequest,
)
from ..auto_indexer import get_auto_indexer
from ..storage.plan_store import DevPlanStore

router = APIRouter(prefix="/devplans", tags=["devplans"])


@router.post("/", response_model=PlanDetail, status_code=status.HTTP_201_CREATED)
async def create_devplan(
    payload: PlanCreate,
    session: AsyncSession = Depends(get_session),
):
    store = DevPlanStore(session)
    plan = await store.create_plan(
        project_id=payload.project_id,
        title=payload.title,
        content=payload.content,
        status=payload.status,
        metadata=payload.metadata,
        conversation_id=payload.conversation_id,
        change_summary=payload.change_summary,
    )
    plan = await store.get_plan(plan.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load created plan")
    try:
        await get_auto_indexer().on_plan_created(plan, content=payload.content)
    except Exception as exc:  # pragma: no cover
        logger.warning("Auto-indexing plan failed: %s", exc)
    return PlanDetail.from_orm(plan)


@router.get("/{plan_id}", response_model=PlanDetail)
async def get_devplan(plan_id: str, session: AsyncSession = Depends(get_session)):
    store = DevPlanStore(session)
    plan = await store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    latest_version = next((v for v in plan.versions if v.version_number == plan.current_version), None)
    try:
        await get_auto_indexer().on_plan_updated(plan, content=(latest_version.content if latest_version else ""))
    except Exception as exc:  # pragma: no cover
        logger.warning("Plan metadata re-index failed: %s", exc)
    return PlanDetail.from_orm(plan)


@router.put("/{plan_id}", response_model=PlanDetail)
async def update_devplan(
    plan_id: str,
    payload: PlanUpdate,
    session: AsyncSession = Depends(get_session),
):
    store = DevPlanStore(session)
    await store.update_plan(
        plan_id,
        title=payload.title,
        status=payload.status,
        metadata=payload.metadata,
        conversation_id=payload.conversation_id,
    )
    plan = await store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanDetail.from_orm(plan)


@router.get("/{plan_id}/versions", response_model=List[PlanVersion])
async def get_devplan_versions(plan_id: str, session: AsyncSession = Depends(get_session)):
    store = DevPlanStore(session)
    versions = await store.get_versions(plan_id)
    return [PlanVersion.from_orm(version) for version in versions]


@router.post("/{plan_id}/versions", response_model=PlanVersion, status_code=status.HTTP_201_CREATED)
async def create_devplan_version(
    plan_id: str,
    payload: VersionCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    store = DevPlanStore(session)
    version = await store.create_version(
        plan_id,
        content=payload.content,
        change_summary=payload.change_summary,
        metadata=payload.metadata,
    )
    plan = await store.get_plan(plan_id)
    if plan:
        try:
            await get_auto_indexer().on_plan_updated(plan, content=payload.content)
        except Exception as exc:  # pragma: no cover
            logger.warning("Plan version re-index failed: %s", exc)
    return PlanVersion.from_orm(version)


@router.get("/{plan_id}/export", response_model=PlanExportResponse)
async def export_devplan(
    plan_id: str,
    format: str = Query(default="markdown"),
    session: AsyncSession = Depends(get_session),
):
    store = DevPlanStore(session)
    export = await store.export_plan(plan_id, export_format=format)
    return PlanExportResponse(**export)


@router.patch("/{plan_id}/status", response_model=PlanDetail)
async def update_plan_status(
    plan_id: str,
    status: str = Query(..., description="New status: draft, approved, in_progress, completed, archived"),
    session: AsyncSession = Depends(get_session),
):
    """Quick action to update plan status."""
    valid_statuses = ["draft", "approved", "in_progress", "completed", "archived"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    store = DevPlanStore(session)
    await store.update_plan(plan_id, status=status)
    plan = await store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    logger.info(f"Plan {plan_id} status updated to {status}")
    return PlanDetail.from_orm(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_devplan(plan_id: str, session: AsyncSession = Depends(get_session)):
    store = DevPlanStore(session)
    await store.delete_plan(plan_id)
    try:
        await get_auto_indexer().on_plan_deleted(plan_id)
    except Exception as exc:  # pragma: no cover
        logger.warning("Plan index removal failed: %s", exc)
    return None
