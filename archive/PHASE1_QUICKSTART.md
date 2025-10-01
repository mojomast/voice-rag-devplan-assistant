# Phase 1 Quick Start Guide
> **Update — 2025-09-30:** Phases 1 & 2 are complete. Use `docs/DEVPLANNING_SETUP.md` for the current end-to-end setup; keep this guide handy for historical Phase 1 implementation details.
## Core Data Layer & API Implementation

This guide will help you implement Phase 1 of the Development Planning feature in 1-2 days.

---

## 📋 Prerequisites

```bash
# Install additional dependencies
pip install sqlalchemy alembic psycopg2-binary python-dateutil
```

Add to `requirements.txt`:
```
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
python-dateutil>=2.8.0
```

---

## 🏗️ Step 1: Database Setup (30 minutes)

### 1.1 Create Database Configuration

**File**: `backend/database.py`

```python
"""
Database configuration and connection management.
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

try:
    from .config import settings
except ImportError:
    from config import settings

# Database URL
# For now, use SQLite for simplicity (can switch to PostgreSQL later)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{settings.VECTOR_STORE_PATH}/../planning.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get database session.
    
    Usage:
        @app.get("/projects")
        def get_projects(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def reset_db():
    """Drop all tables and recreate (for development only)."""
    logger.warning("Resetting database - all data will be lost!")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete")
```

### 1.2 Create Data Models

**File**: `backend/models.py`

```python
"""
SQLAlchemy models for development planning system.
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from pydantic import BaseModel as PydanticBaseModel

try:
    from .database import Base
except ImportError:
    from database import Base


# SQLAlchemy Models (for database)

class Project(Base):
    """Project entity - represents a development project."""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", index=True)  # active, paused, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    repository_path = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # List of tags
    
    # Relationships
    plans = relationship("DevPlan", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("ConversationSession", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_status_created', 'status', 'created_at'),
    )


class DevPlan(Base):
    """Development Plan entity - represents a project plan with versioning."""
    __tablename__ = "devplans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    status = Column(String(50), default="draft", index=True)  # draft, approved, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    conversation_id = Column(String(36), nullable=True)  # Reference to conversation that created it
    metadata = Column(JSON, default=dict)  # Additional metadata (estimates, milestones, etc.)
    
    # Relationships
    project = relationship("Project", back_populates="plans")
    
    # Indexes
    __table_args__ = (
        Index('idx_devplan_project_version', 'project_id', 'version'),
        Index('idx_devplan_status_created', 'status', 'created_at'),
    )


class ConversationSession(Base):
    """Conversation Session - tracks planning conversations."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    messages = Column(JSON, default=list)  # List of message dicts
    summary = Column(Text, nullable=True)  # AI-generated summary
    generated_plan_ids = Column(JSON, default=list)  # List of plan IDs created in this session
    
    # Relationships
    project = relationship("Project", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_project_started', 'project_id', 'started_at'),
    )


# Pydantic Models (for API request/response)

class ProjectCreate(PydanticBaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = None
    repository_path: Optional[str] = None
    tags: List[str] = []


class ProjectUpdate(PydanticBaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    repository_path: Optional[str] = None
    tags: Optional[List[str]] = None


class ProjectResponse(PydanticBaseModel):
    """Response model for project data."""
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    repository_path: Optional[str]
    tags: List[str]
    plan_count: int = 0
    conversation_count: int = 0
    
    class Config:
        from_attributes = True


class DevPlanCreate(PydanticBaseModel):
    """Request model for creating a devplan."""
    project_id: str
    title: str
    content: str
    conversation_id: Optional[str] = None
    metadata: dict = {}


class DevPlanUpdate(PydanticBaseModel):
    """Request model for updating a devplan."""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class DevPlanResponse(PydanticBaseModel):
    """Response model for devplan data."""
    id: str
    project_id: str
    version: int
    title: str
    content: str
    status: str
    created_at: datetime
    conversation_id: Optional[str]
    metadata: dict
    
    class Config:
        from_attributes = True


class ConversationMessage(PydanticBaseModel):
    """Single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    modality: str = "text"  # "text" or "voice"


class ConversationSessionCreate(PydanticBaseModel):
    """Request model for starting a conversation."""
    project_id: Optional[str] = None


class ConversationSessionResponse(PydanticBaseModel):
    """Response model for conversation session."""
    id: str
    project_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    messages: List[dict]
    summary: Optional[str]
    generated_plan_ids: List[str]
    
    class Config:
        from_attributes = True
```

---

## 🔧 Step 2: Storage Layer (45 minutes)

### 2.1 Project Store

**File**: `backend/storage/project_store.py`

```python
"""
Project storage and CRUD operations.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from loguru import logger

try:
    from ..models import Project, ProjectCreate, ProjectUpdate, ProjectResponse
except ImportError:
    from models import Project, ProjectCreate, ProjectUpdate, ProjectResponse


class ProjectStore:
    """Handles all project data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(
            name=project_data.name,
            description=project_data.description,
            repository_path=project_data.repository_path,
            tags=project_data.tags,
            status="active"
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        logger.info(f"Created project: {project.name} (ID: {project.id})")
        return project
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self.db.query(Project).filter(Project.id == project_id).first()
    
    def list_all(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "updated_at",
        ascending: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Project]:
        """List projects with optional filtering and sorting."""
        query = self.db.query(Project)
        
        # Apply filters
        if status:
            query = query.filter(Project.status == status)
        
        # TODO: Add tag filtering (requires JSON query capabilities)
        
        # Apply sorting
        sort_column = getattr(Project, sort_by, Project.updated_at)
        query = query.order_by(asc(sort_column) if ascending else desc(sort_column))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update(self, project_id: str, updates: ProjectUpdate) -> Optional[Project]:
        """Update project fields."""
        project = self.get(project_id)
        if not project:
            return None
        
        # Update fields if provided
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        logger.info(f"Updated project: {project.name} (ID: {project.id})")
        return project
    
    def delete(self, project_id: str) -> bool:
        """Delete (or archive) a project."""
        project = self.get(project_id)
        if not project:
            return False
        
        # Instead of hard delete, archive it
        project.status = "archived"
        project.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Archived project: {project.name} (ID: {project.id})")
        return True
    
    def search(self, query: str, limit: int = 10) -> List[Project]:
        """Search projects by name or description."""
        search_term = f"%{query}%"
        return self.db.query(Project).filter(
            (Project.name.ilike(search_term)) | 
            (Project.description.ilike(search_term))
        ).limit(limit).all()
    
    def get_with_stats(self, project_id: str) -> Optional[dict]:
        """Get project with associated stats (plan count, conversation count)."""
        project = self.get(project_id)
        if not project:
            return None
        
        return {
            "project": project,
            "plan_count": len(project.plans),
            "conversation_count": len(project.conversations),
            "latest_plan": project.plans[-1] if project.plans else None,
            "latest_conversation": project.conversations[-1] if project.conversations else None
        }
```

### 2.2 Plan Store

**File**: `backend/storage/plan_store.py`

```python
"""
DevPlan storage and version management.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

try:
    from ..models import DevPlan, DevPlanCreate, DevPlanUpdate, DevPlanResponse
except ImportError:
    from models import DevPlan, DevPlanCreate, DevPlanUpdate, DevPlanResponse


class PlanStore:
    """Handles all devplan data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, plan_data: DevPlanCreate) -> DevPlan:
        """Create a new devplan (version 1)."""
        # Check if there are existing plans for this project
        existing_count = self.db.query(DevPlan).filter(
            DevPlan.project_id == plan_data.project_id
        ).count()
        
        plan = DevPlan(
            project_id=plan_data.project_id,
            title=plan_data.title,
            content=plan_data.content,
            conversation_id=plan_data.conversation_id,
            metadata=plan_data.metadata,
            version=existing_count + 1,
            status="draft"
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Created devplan: {plan.title} (ID: {plan.id}, Version: {plan.version})")
        return plan
    
    def get(self, plan_id: str) -> Optional[DevPlan]:
        """Get plan by ID."""
        return self.db.query(DevPlan).filter(DevPlan.id == plan_id).first()
    
    def get_by_project(
        self,
        project_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[DevPlan]:
        """Get all plans for a project."""
        query = self.db.query(DevPlan).filter(DevPlan.project_id == project_id)
        
        if status:
            query = query.filter(DevPlan.status == status)
        
        query = query.order_by(desc(DevPlan.created_at)).limit(limit)
        return query.all()
    
    def update(self, plan_id: str, updates: DevPlanUpdate) -> Optional[DevPlan]:
        """Update plan fields."""
        plan = self.get(plan_id)
        if not plan:
            return None
        
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Updated devplan: {plan.title} (ID: {plan.id})")
        return plan
    
    def create_version(self, plan_id: str, changes: str) -> Optional[DevPlan]:
        """Create a new version of an existing plan."""
        original = self.get(plan_id)
        if not original:
            return None
        
        # Get the highest version for this project
        max_version = self.db.query(DevPlan).filter(
            DevPlan.project_id == original.project_id
        ).count()
        
        new_plan = DevPlan(
            project_id=original.project_id,
            title=original.title,
            content=changes,
            version=max_version + 1,
            status="draft",
            metadata=original.metadata.copy()
        )
        self.db.add(new_plan)
        self.db.commit()
        self.db.refresh(new_plan)
        logger.info(f"Created version {new_plan.version} of devplan: {new_plan.title}")
        return new_plan
    
    def get_versions(self, project_id: str) -> List[DevPlan]:
        """Get all versions of plans for a project."""
        return self.db.query(DevPlan).filter(
            DevPlan.project_id == project_id
        ).order_by(DevPlan.version).all()
    
    def delete(self, plan_id: str) -> bool:
        """Delete a plan."""
        plan = self.get(plan_id)
        if not plan:
            return False
        
        self.db.delete(plan)
        self.db.commit()
        logger.info(f"Deleted devplan: {plan.title} (ID: {plan.id})")
        return True
```

### 2.3 Conversation Store

**File**: `backend/storage/conversation_store.py`

```python
"""
Conversation session storage and management.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

try:
    from ..models import ConversationSession, ConversationSessionCreate, ConversationMessage
except ImportError:
    from models import ConversationSession, ConversationSessionCreate, ConversationMessage


class ConversationStore:
    """Handles conversation session data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, session_data: ConversationSessionCreate) -> ConversationSession:
        """Start a new conversation session."""
        session = ConversationSession(
            project_id=session_data.project_id,
            messages=[],
            generated_plan_ids=[]
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Created conversation session: {session.id}")
        return session
    
    def get(self, session_id: str) -> Optional[ConversationSession]:
        """Get session by ID."""
        return self.db.query(ConversationSession).filter(
            ConversationSession.id == session_id
        ).first()
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        modality: str = "text"
    ) -> Optional[ConversationSession]:
        """Add a message to the conversation."""
        session = self.get(session_id)
        if not session:
            return None
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality
        }
        
        messages = session.messages or []
        messages.append(message)
        session.messages = messages
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def end_session(self, session_id: str, summary: Optional[str] = None) -> Optional[ConversationSession]:
        """End a conversation session."""
        session = self.get(session_id)
        if not session:
            return None
        
        session.ended_at = datetime.utcnow()
        if summary:
            session.summary = summary
        
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Ended conversation session: {session.id}")
        return session
    
    def get_by_project(self, project_id: str, limit: int = 50) -> List[ConversationSession]:
        """Get all conversations for a project."""
        return self.db.query(ConversationSession).filter(
            ConversationSession.project_id == project_id
        ).order_by(desc(ConversationSession.started_at)).limit(limit).all()
    
    def link_plan(self, session_id: str, plan_id: str) -> Optional[ConversationSession]:
        """Link a generated plan to this conversation."""
        session = self.get(session_id)
        if not session:
            return None
        
        plan_ids = session.generated_plan_ids or []
        if plan_id not in plan_ids:
            plan_ids.append(plan_id)
            session.generated_plan_ids = plan_ids
            self.db.commit()
            self.db.refresh(session)
        
        return session
```

---

## 🌐 Step 3: API Endpoints (60 minutes)

### 3.1 Project Endpoints

**File**: `backend/routers/projects.py`

```python
"""
Project management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

try:
    from ..database import get_db
    from ..models import ProjectCreate, ProjectUpdate, ProjectResponse
    from ..storage.project_store import ProjectStore
except ImportError:
    from database import get_db
    from models import ProjectCreate, ProjectUpdate, ProjectResponse
    from storage.project_store import ProjectStore

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project."""
    store = ProjectStore(db)
    new_project = store.create(project)
    
    # Build response with stats
    return ProjectResponse(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        status=new_project.status,
        created_at=new_project.created_at,
        updated_at=new_project.updated_at,
        repository_path=new_project.repository_path,
        tags=new_project.tags or [],
        plan_count=0,
        conversation_count=0
    )


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("updated_at", description="Sort field"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all projects with optional filtering."""
    store = ProjectStore(db)
    projects = store.list_all(status=status, sort_by=sort_by, limit=limit, offset=offset)
    
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
            repository_path=p.repository_path,
            tags=p.tags or [],
            plan_count=len(p.plans),
            conversation_count=len(p.conversations)
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project details."""
    store = ProjectStore(db)
    project = store.get(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        repository_path=project.repository_path,
        tags=project.tags or [],
        plan_count=len(project.plans),
        conversation_count=len(project.conversations)
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    updates: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update project details."""
    store = ProjectStore(db)
    project = store.update(project_id, updates)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        repository_path=project.repository_path,
        tags=project.tags or [],
        plan_count=len(project.plans),
        conversation_count=len(project.conversations)
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Archive a project."""
    store = ProjectStore(db)
    success = store.delete(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return None


@router.get("/{project_id}/plans")
def get_project_plans(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all plans for a project."""
    from storage.plan_store import PlanStore
    
    store = ProjectStore(db)
    project = store.get(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    plan_store = PlanStore(db)
    plans = plan_store.get_by_project(project_id)
    
    return {"project_id": project_id, "plans": plans}
```

Now create similar routers for devplans and conversations...

---

## 🚀 Step 4: Integrate with Main App (15 minutes)

**Update**: `backend/main.py`

```python
# Add at the top with other imports
try:
    from .database import init_db
    from .routers import projects, devplans, planning_chat
except ImportError:
    from database import init_db
    from routers import projects, devplans, planning_chat

# After app initialization (around line 70)
# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize systems on startup."""
    logger.info("Starting up Voice-Enabled RAG System")
    
    # Initialize planning database
    try:
        init_db()
        logger.info("Planning database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize monitoring systems
    initialize_monitoring_system()
    initialize_performance_optimizations()
    initialize_security_system()

# Include routers (after line 200 or so)
app.include_router(projects.router)
# app.include_router(devplans.router)  # Create this next
# app.include_router(planning_chat.router)  # Create this in Phase 2
```

---

## ✅ Testing Phase 1 (15 minutes)

### Test the API

```bash
# Start your backend
C:\Users\kyle\projects\noteagent\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# In another terminal, test the endpoints:

# Create a project
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "voice-rag-system",
    "description": "Voice-enabled document Q&A system",
    "tags": ["ai", "rag", "voice"]
  }'

# List projects
curl http://localhost:8000/projects/

# Get specific project
curl http://localhost:8000/projects/{project_id}

# Update project
curl -X PUT http://localhost:8000/projects/{project_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

Or test via the interactive docs at: `http://localhost:8000/docs`

---

## 📝 Next Steps

After completing Phase 1, you'll have:

✅ Database setup with SQLAlchemy models
✅ Storage layer for projects, plans, and conversations
✅ REST API for project management
✅ Foundation for Phase 2 (LLM Planning Agent)

**Move on to Phase 2** to add the Planning Agent that will use these data structures to have intelligent conversations about development planning.

---

## 🎯 Summary

Phase 1 Runtime: **~2-3 hours**

You now have:
- ✅ Database schema and models
- ✅ CRUD operations for projects
- ✅ API endpoints for project management
- ✅ Foundation for devplans and conversations

**Ready for Phase 2**: LLM Planning Agent integration!
