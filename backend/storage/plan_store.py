"""Development plan persistence utilities."""

from __future__ import annotations

from collections.abc import Iterable
from difflib import unified_diff
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import DevPlan, DevPlanVersion, PlanStatus


class DevPlanStore:
    """CRUD operations and version management for development plans."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(
        self,
        *,
        project_id: str,
        title: str,
        content: str,
        status: PlanStatus = PlanStatus.DRAFT,
        metadata: Optional[dict] = None,
        conversation_id: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> DevPlan:
        plan = DevPlan(
            project_id=project_id,
            title=title,
            status=status.value if isinstance(status, PlanStatus) else status,
            metadata_dict=metadata or {},
            conversation_id=conversation_id,
            current_version=1,
        )
        version = DevPlanVersion(
            plan=plan,
            version_number=1,
            content=content,
            change_summary=change_summary,
        )
        self.session.add(plan)
        self.session.add(version)
        await self.session.flush()
        return plan

    async def get_plan(self, plan_id: str, include_versions: bool = True) -> Optional[DevPlan]:
        stmt = select(DevPlan).where(DevPlan.id == plan_id)
        if include_versions:
            stmt = stmt.options(joinedload(DevPlan.versions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        *,
        project_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DevPlan]:
        stmt: Select = select(DevPlan).order_by(DevPlan.updated_at.desc())
        if project_id:
            stmt = stmt.where(DevPlan.project_id == project_id)
        if status:
            value = status.value if isinstance(status, PlanStatus) else status
            stmt = stmt.where(DevPlan.status == value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_plan(
        self,
        plan_id: str,
        *,
        title: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        metadata: Optional[dict] = None,
        conversation_id: Optional[str] = None,
    ) -> DevPlan:
        plan = await self.get_plan(plan_id, include_versions=False)
        if not plan:
            raise NoResultFound(f"Plan {plan_id} not found")

        if title is not None:
            plan.title = title
        if status is not None:
            plan.status = status.value if isinstance(status, PlanStatus) else status
        if metadata is not None:
            plan.metadata_dict = metadata
        if conversation_id is not None:
            plan.conversation_id = conversation_id

        await self.session.flush()
        return plan

    async def create_version(
        self,
        plan_id: str,
        *,
        content: str,
        change_summary: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DevPlanVersion:
        plan = await self.get_plan(plan_id, include_versions=False)
        if not plan:
            raise NoResultFound(f"Plan {plan_id} not found")

        next_version = plan.current_version + 1
        version = DevPlanVersion(
            plan_id=plan_id,
            version_number=next_version,
            content=content,
            change_summary=change_summary,
            metadata_dict=metadata or {},
        )
        plan.current_version = next_version
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_versions(self, plan_id: str) -> list[DevPlanVersion]:
        stmt = (
            select(DevPlanVersion)
            .where(DevPlanVersion.plan_id == plan_id)
            .order_by(DevPlanVersion.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_plan(self, plan_id: str) -> None:
        plan = await self.get_plan(plan_id, include_versions=False)
        if not plan:
            raise NoResultFound(f"Plan {plan_id} not found")
        plan.status = PlanStatus.ARCHIVED.value
        await self.session.flush()

    async def export_plan(self, plan_id: str, export_format: str = "markdown") -> dict:
        plan = await self.get_plan(plan_id)
        if not plan:
            raise NoResultFound(f"Plan {plan_id} not found")
        latest_version = next((v for v in plan.versions if v.version_number == plan.current_version), None)
        content = latest_version.content if latest_version else ""
        return {
            "plan_id": plan.id,
            "title": plan.title,
            "version": plan.current_version,
            "format": export_format,
            "content": content,
            "metadata": plan.metadata_dict,
        }

    async def diff_versions(
        self, plan_id: str, from_version: int, to_version: int
    ) -> str:
        versions = await self.get_versions(plan_id)
        from_doc = next((v.content for v in versions if v.version_number == from_version), "")
        to_doc = next((v.content for v in versions if v.version_number == to_version), "")
        diff_lines = unified_diff(
            from_doc.splitlines(),
            to_doc.splitlines(),
            fromfile=f"v{from_version}",
            tofile=f"v{to_version}",
            lineterm="",
        )
        return "\n".join(diff_lines)
