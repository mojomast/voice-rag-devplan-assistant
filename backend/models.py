"""SQLAlchemy models for development planning entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    """Mixin providing created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.ACTIVE.value)
    repository_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan_count: Mapped[int] = mapped_column(Integer, default=0)
    conversation_count: Mapped[int] = mapped_column(Integer, default=0)
    tags = Column(MutableList.as_mutable(JSON), default=list)

    devplans: Mapped[list["DevPlan"]] = relationship(
        "DevPlan",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    conversations: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_project_name"),
        {"extend_existing": True},
    )


class ConversationSession(TimestampMixin, Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_plans = Column(MutableList.as_mutable(JSON), default=list)

    project: Mapped[Optional[Project]] = relationship("Project", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        order_by="ConversationMessage.timestamp",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    plans: Mapped[list["DevPlan"]] = relationship(
        "DevPlan",
        back_populates="conversation",
    )

    __table_args__ = ({"extend_existing": True},)


class DevPlan(TimestampMixin, Base):
    __tablename__ = "devplans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(PlanStatus), default=PlanStatus.DRAFT.value)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversation_sessions.id", ondelete="SET NULL"), nullable=True
    )
    metadata_dict: Mapped[dict[str, Any]] = mapped_column(
        "metadata", MutableDict.as_mutable(JSON), default=dict
    )

    project: Mapped[Project] = relationship("Project", back_populates="devplans")
    conversation: Mapped[Optional[ConversationSession]] = relationship(
        "ConversationSession", back_populates="plans"
    )
    versions: Mapped[list["DevPlanVersion"]] = relationship(
        "DevPlanVersion",
        order_by="DevPlanVersion.version_number.desc()",
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = ({"extend_existing": True},)


class DevPlanVersion(TimestampMixin, Base):
    __tablename__ = "devplan_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devplans.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_dict: Mapped[dict[str, Any]] = mapped_column(
        "metadata", MutableDict.as_mutable(JSON), default=dict
    )

    plan: Mapped[DevPlan] = relationship("DevPlan", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("plan_id", "version_number", name="uq_plan_version"),
        {"extend_existing": True},
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    modality: Mapped[str] = mapped_column(String(20), default="text")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    session: Mapped[ConversationSession] = relationship("ConversationSession", back_populates="messages")

    __table_args__ = ({"extend_existing": True},)