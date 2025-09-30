"""Project persistence utilities."""

from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import Select, func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Project, ProjectStatus


class ProjectStore:
    """CRUD operations for project entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(
        self,
        *,
        name: str,
        description: str = "",
        status: ProjectStatus = ProjectStatus.ACTIVE,
        tags: Optional[list[str]] = None,
        repository_path: Optional[str] = None,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            status=status.value if isinstance(status, ProjectStatus) else status,
            tags=tags or [],
            repository_path=repository_path,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_project(self, project_id: str, *, include_counts: bool = True) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id)
        if include_counts:
            stmt = stmt.options(joinedload(Project.devplans), joinedload(Project.conversations))

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_projects(
        self,
        *,
        status: Optional[ProjectStatus] = None,
        search: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        stmt: Select = select(Project).order_by(Project.updated_at.desc())

        if status:
            value = status.value if isinstance(status, ProjectStatus) else status
            stmt = stmt.where(Project.status == value)

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Project.name).like(like) | func.lower(Project.description).like(like))

        if tags:
            for tag in tags:
                stmt = stmt.where(Project.tags.contains([tag]))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        tags: Optional[list[str]] = None,
        repository_path: Optional[str] = None,
    ) -> Project:
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        project = result.unique().scalar_one_or_none()
        if project is None:
            raise NoResultFound(f"Project {project_id} not found")

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status.value if isinstance(status, ProjectStatus) else status
        if tags is not None:
            project.tags = tags
        if repository_path is not None:
            project.repository_path = repository_path

        await self.session.flush()
        return project

    async def archive_project(self, project_id: str) -> Project:
        project = await self.get_project(project_id)
        if not project:
            raise NoResultFound(f"Project {project_id} not found")

        project.status = ProjectStatus.ARCHIVED.value
        await self.session.flush()
        return project

    async def get_project_with_stats(self, project_id: str) -> Optional[Project]:
        stmt = (
            select(Project)
            .options(joinedload(Project.devplans), joinedload(Project.conversations))
            .where(Project.id == project_id)
        )
        result = await self.session.execute(stmt)
        project = result.unique().scalar_one_or_none()
        if project:
            project.plan_count = len(project.devplans)
            project.conversation_count = len(project.conversations)
        return project
