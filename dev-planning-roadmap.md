# Development Planning Feature - Implementation Roadmap

Transform the voice-rag-system into an intelligent development planning assistant that helps developers create and iterate on development plans via conversational LLM, remembers all projects and past conversations, allows voice and text interaction for creating devplans, persists all planning documents and iterations in the vector store, and provides project-aware context for continuing work across sessions.

> **Status Snapshot — 2025-10-01 (FINAL PHASE 3 UPDATE)**
>
> • **Phase 1 complete**: Async database layer, SQLAlchemy models, storage services, FastAPI routers, and unit tests are live.<br>
> • **Phase 2 complete**: `PlanningAgent`, `DevPlanGenerator`, and `PlanningContextManager` implemented with Requesty integration; comprehensive test suite (29 tests); structured telemetry.<br>
> • **Phase 3 COMPLETE**: Full-featured production UI delivered including real-time auto-refresh, quick action buttons, project health widgets, prompt template library (9 templates), enhanced notifications, status visualization, frontend telemetry system, accessibility guidelines, and E2E test framework.<br>
> • **Phase 4 READY**: See `nextphase.md` for RAG Integration & Indexing implementation roadmap.

## Phase Progress Dashboard

| Phase | Scope | Status (2025-09-30) | Notes |
|-------|-------|----------------------|-------|
| Phase 1 | Core data layer & REST APIs | ✅ Completed | Backend models (`backend/models.py`), stores (`backend/storage/`), routers, migrations, and unit tests shipped. |
| Phase 2 | LLM planning agent & Requesty integration | ✅ Completed (2025-09-30) | `PlanningAgent`, `DevPlanGenerator`, `PlanningContextManager` with Requesty integration, comprehensive test coverage (29 tests), and telemetry logging. |
|| Phase 3 | Frontend experience | ✅ Completed (2025-10-01) | Production-ready UI: real-time refresh, quick actions, health widgets, prompt templates, notifications, telemetry, accessibility docs, E2E test framework. |
|| Phase 4 | RAG indexing & memory | 🚀 Ready to start | Vector-store ingest for plans/projects; semantic search and context retrieval. See `nextphase.md` for roadmap. |
| Phase 5+ | Voice + advanced features | ⏳ Future | Voice planning pipeline, collaboration, analytics, etc. |

## Delivered in Phase 1 (Summary)

- **Database & ORM**: Async SQLAlchemy engine (`backend/database.py`), declarative models with enumerated statuses and metadata handling (`backend/models.py`).
- **Storage Services**: `ProjectStore`, `DevPlanStore`, and `ConversationStore` with CRUD, filtering, versioning, exports, and session lifecycle support.
- **API Surface**: FastAPI routers for `/projects`, `/devplans`, and `/planning` registered in `backend/main.py`; planning chat currently returns a placeholder.
- **Migrations & Config**: Seed SQL in `backend/migrations/001-003_*.sql`; `backend/config.py` now configures `DATABASE_URL`, creates SQLite data dir automatically.
- **Testing**: Targeted async unit tests in `tests/unit/test_project_store.py`, `test_plan_store.py`, and `test_conversation_store.py` (all green with `python -m pytest tests/unit/test_project_store.py tests/unit/test_plan_store.py tests/unit/test_conversation_store.py -q`).
- **Documentation**: `PHASE1_QUICKSTART.md`, `docs/DEVPLANNING_SETUP.md`, and `PROJECT_STATUS.md` updated to reflect the new backend and outline next steps.

## Next-Agent Jumpstart Checklist (Phase 2)

- [x] **Planning Agent Core**
    - `PlanningAgent`, `DevPlanGenerator`, and `PlanningContextManager` implemented with Requesty-powered orchestration.
    - `/planning/chat` now invokes the real agent pipeline and persists generated plans.
- [x] **Requesty Integration**
    - `backend/requesty_client.py` upgraded for Requesty Router models (`requesty/glm-4.5`, `requesty/embedding-001`) plus async wrappers and deterministic test fallbacks.
    - `docs/DEVPLANNING_SETUP.md` updated with credential guidance and tunable planning parameters.
- [x] **Testing & Telemetry**
    - ✅ Unit tests added: `tests/unit/test_planning_agent.py` (6 tests), `tests/unit/test_plan_generator.py` (10 tests)
    - ✅ Integration tests added: `tests/integration/test_planning_chat.py` (13 endpoint tests)
    - ✅ Telemetry implemented: Structured logging with timing metrics in `planning_agent.py` and `plan_generator.py`
    - ✅ All tests passing: 16 unit tests + 13 integration tests covering agent flows, Requesty fallbacks, and E2E scenarios

Refer back to the detailed Phase sections below for design intent, but treat the checklist above as the canonical starting point.

## 🧠 LLM & API Assignments

The system leverages a hybrid approach using both Requesty and OpenAI APIs for optimal cost-effectiveness and performance:

| Component | Model | API Provider | Purpose |
|-----------|-------|--------------|---------|
| Planning Agent (Conversations, DevPlan generation) | `glm-4.5` (or requesty-available reasoning model) | **Requesty** | Conversational planning, devplan drafting, context-aware iteration |
| RAG Context Retrieval (Embeddings + Similarity) | `embedding-001` | **Requesty** | Embedding devplans/projects, semantic search, context retrieval |
| Document Generation (Markdown/JSON structured plans) | `glm-4.5` | **Requesty** | Structured document creation, JSON/Markdown outputs |
| Voice Input (ASR) | `whisper-1` | **OpenAI** | Transcribe planning discussions |
| Voice Output (TTS) | `gpt-4o-mini-tts` | **OpenAI** | Speak planning agent responses |

This configuration maximizes the utilization of existing Requesty credits for core planning functionality while leveraging OpenAI's superior voice capabilities where needed.

## 📋 Core Requirements

### Primary Use Case
**As a developer**, the system enables users to:
1. Chat (via voice or text) with an LLM to develop project plans
2. Have the system remember all projects worked on previously
3. Return weeks later and continue iterating on existing plans
4. Have the assistant automatically reference past work when relevant
5. Generate structured devplan documents that are searchable and editable

### Key Capabilities Needed
- ✅ **Project Memory**: Track all projects discussed in conversations
- ✅ **Plan Versioning**: Store iterations of development plans over time
- ✅ **Context Awareness**: LLM knows about previous projects when creating new ones
- ✅ **Document Generation**: Auto-generate markdown devplan documents
- ✅ **Search & Retrieval**: Query past projects and plans via RAG
- ✅ **Edit & Update**: Modify existing plans through conversation

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Development Planning System                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Frontend   │    │   Backend    │    │   Storage    │     │
│  │              │    │              │    │              │     │
│  │ • Chat UI    │◄──►│ • Plan API   │◄──►│ • Projects   │     │
│  │ • Voice      │    │ • LLM Agent  │    │ • Devplans   │     │
│  │ • Project    │    │ • RAG        │    │ • Vectors    │     │
│  │   Browser    │    │ • Versioning │    │ • Metadata   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Project & Plan Management                   │  │
│  │                                                          │  │
│  │  • Project Tracker: Maintains list of all projects      │  │
│  │  • Plan Versioning: Tracks iterations over time         │  │
│  │  • Context Manager: Provides relevant history to LLM    │  │
│  │  • Document Generator: Creates structured devplans      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

The system employs a three-layer architecture with specialized LLM/API assignments for different components. The frontend provides chat UI, voice interaction, and project browsing capabilities. The backend handles plan APIs, LLM agent interactions using glm-4.5 via Requesty, RAG operations with embedding-001, and versioning. The storage layer manages projects, devplans, vectors, and metadata in both structured and vector formats.

## 📊 Data Model

### Project Entity
```python
{
    "project_id": "uuid",
    "name": "voice-rag-system",
    "description": "Voice-enabled document Q&A system",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z",
    "status": "active",  # active, paused, completed, archived
    "tags": ["ai", "rag", "voice", "fastapi"],
    "repository_path": "/path/to/repo",
    "plan_count": 5,
    "conversation_count": 12
}
```

### DevPlan Entity
```python
{
    "plan_id": "uuid",
    "project_id": "uuid",
    "version": 3,
    "title": "Add Development Planning Feature",
    "created_at": "2025-01-20T15:30:00Z",
    "content": "# Full markdown content...",
    "status": "draft",  # draft, approved, in_progress, completed
    "conversation_id": "uuid",  # Link to conversation that created it
    "sections": [
        {"title": "Phase 1", "content": "...", "order": 1},
        {"title": "Phase 2", "content": "...", "order": 2}
    ],
    "metadata": {
        "estimated_hours": 40,
        "priority": "high",
        "dependencies": [],
        "milestones": []
    }
}
```

### Conversation Session
```python
{
    "session_id": "uuid",
    "project_id": "uuid",  # Optional, if working on specific project
    "started_at": "2025-01-20T15:00:00Z",
    "ended_at": "2025-01-20T16:30:00Z",
    "messages": [
        {
            "role": "user",
            "content": "Help me plan the devplan feature",
            "timestamp": "2025-01-20T15:00:00Z",
            "modality": "voice"
        },
        {
            "role": "assistant",
            "content": "I'll help you plan that...",
            "timestamp": "2025-01-20T15:00:15Z"
        }
    ],
    "generated_plans": ["plan_id_1", "plan_id_2"],
    "summary": "Discussed adding development planning feature to voice-rag-system"
}
```

## 🔧 Implementation Phases

### Phase 1: Core Data Layer & API (Week 1)

> **Status:** ✅ Completed on 2025-09-30 — references below describe the implemented code. Retain this section for historical context or for rebuilding environments.

This phase establishes the foundational database and API infrastructure without requiring LLM integration. The implementation focuses on creating SQLAlchemy models for Project, DevPlan, and ConversationSession entities with appropriate relationships and indexes.

#### 1.1 Database Schema
**File**: `backend/models.py`
- Create SQLAlchemy models for Project, DevPlan, ConversationSession
- Add relationships and indexes
- Migration scripts

**File**: `backend/database.py`
- Database connection setup
- Session management
- CRUD operations

#### 1.2 Storage Layer
**File**: `backend/storage/project_store.py`
- ProjectStore class for CRUD operations
- List, filter, search projects
- Archive/restore functionality

**File**: `backend/storage/plan_store.py`
- DevPlanStore class for plan management
- Version tracking and diff generation
- Plan export (markdown, JSON, PDF)

**File**: `backend/storage/conversation_store.py`
- ConversationStore for session management
- Message persistence
- Session summarization

#### 1.3 API Endpoints
**File**: `backend/routers/projects.py`
```python
# Project Management
POST   /projects/                    # Create new project
GET    /projects/                    # List all projects
GET    /projects/{id}                # Get project details
PUT    /projects/{id}                # Update project
DELETE /projects/{id}                # Archive project
GET    /projects/{id}/plans          # Get all plans for project
GET    /projects/{id}/conversations  # Get conversation history
```

**File**: `backend/routers/devplans.py`
```python
# Development Plan Management
POST   /devplans/                    # Create new devplan
GET    /devplans/{id}                # Get specific plan
PUT    /devplans/{id}                # Update existing plan
GET    /devplans/{id}/versions       # Get version history
POST   /devplans/{id}/versions       # Create new version
GET    /devplans/{id}/export         # Export as markdown/PDF
DELETE /devplans/{id}                # Delete plan
```

**File**: `backend/routers/planning_chat.py`
```python
# Planning Chat Interface
POST   /planning/chat                # Send message to planning assistant
GET    /planning/sessions            # List chat sessions
GET    /planning/sessions/{id}       # Get session details
DELETE /planning/sessions/{id}       # Clear session
POST   /planning/generate            # Generate devplan from conversation
```

### Phase 2: LLM Planning Agent (Week 2)

> **Status:** 🔄 Not started — this is the immediate focus for the next development cycle. Use the checklist above and the design below to implement.

This phase introduces the core LLM functionality using **glm-4.5 via Requesty API** for planning conversations and structured devplan generation. The implementation abstracts LLM interactions through `llm_client.py` to enable easy model swapping in the future.

#### 2.1 Planning Agent Core
**File**: `backend/planning_agent.py`
**Delivered:** `backend/planning_agent.py` now orchestrates conversation state, Requesty prompts, and plan generation end-to-end. The agent:

- Builds JSON-only prompts with contextual slices from `PlanningContextManager`.
- Parses structured actions (create/revise plan) with resilient fallbacks for non-JSON output.
- Delegates plan drafting to `DevPlanGenerator`, persisting outputs through `DevPlanStore`.
- Tracks generated plan IDs back onto the conversation session for downstream retrieval.

#### 2.2 Plan Generation & Parsing
**File**: `backend/plan_generator.py`
`backend/plan_generator.py` converts agent intents into Markdown plans:

- Prompts `requesty/glm-4.5` for structured JSON (`plan_title`, `plan_summary`, `plan_markdown`, `metadata`).
- Falls back to deterministic markdown when Requesty keys are absent (TEST_MODE).
- Persists plans and change summaries through `DevPlanStore`, returning the created `DevPlan` object.

#### 2.3 Context Management
**File**: `backend/context_manager.py`
`backend/context_manager.py` assembles prompt-ready context:

- Pulls project stats, latest plans, and recent conversation turns via async stores.
- Taps the Requesty-backed `RAGHandler` when available for semantic hints.
- Normalises results into a prompt section consumed by `PlanningAgent` and `DevPlanGenerator`.

### Phase 3: Frontend Integration (Week 3)

The frontend interfaces with the backend APIs without direct model calls, utilizing Requesty for chat functionality and OpenAI for voice processing through backend endpoints.

#### 3.1 Planning Chat Interface (`frontend/pages/planning_chat.py`)

**Delivered**

- Multi-session planning conversations with persisted history, generated plan tracking, and automatic plan preview loading.
- Voice capture through `native_audio_recorder` with `/voice/transcribe-base64` hand-off, plus inline project creation and selection.
- Error handling and toast-based notifications for API failures, along with plan metadata surfacing inside expandable previews.

**Delivered Enhancements (2025-10-01)**

- ✅ Live refresh of messages and generated plans: 10-second auto-polling with manual refresh button
- ✅ Quick actions for approving/archiving plans: Inline status buttons (Approve, Start, Complete, Archive) with visual feedback
- ✅ Status chips for metadata: Color-coded status indicators throughout UI (draft/approved/in-progress/completed/archived)
- ✅ Saved prompt templates: 9 pre-built templates across Development, Maintenance, Integration, Infrastructure, Security, Testing, Documentation categories

**Outstanding Enhancements**

- Playback of synthesized assistant responses using the TTS stack in session timeline view
- Session timeline visualization showing message + plan generation event history

#### 3.2 Project Browser (`frontend/pages/project_browser.py`)

**Delivered**

- Server-driven project list with search, status filters, and tag filtering; metrics for plan and conversation counts per project.
- Detail pane that surfaces latest plans, quick-open shortcuts into planning chat and devplan viewer, and conversation summaries.
- Session state wiring so cross-page navigation (project → chat/viewer) keeps context without re-selecting items.

**Delivered Enhancements (2025-10-01)**

- ✅ Project health snapshot widgets: Health score calculation, completed/in-progress metrics, latest plan status chips
- ✅ Status visualization: Color-coded project and plan status indicators throughout the browser

**Outstanding Enhancements**

- RAG-driven "related projects" sidebar and quick filters (e.g., show projects missing approved plans)
- Bulk operations (archive, tag, export) and CSV/Markdown export of project summaries for stakeholder reporting
- Highlight recently updated conversations and expose agent confidence / telemetry metrics

#### 3.3 DevPlan Viewer & Editor (`frontend/pages/devplan_viewer.py`)

**Delivered**

- Metadata sidebar, markdown rendering, JSON/markdown exports, and version history with unified diffs between selected versions.
- Plan metadata editing (title/status/metadata), new version creation with change summaries, and version-level metadata overrides.
- Automatic project/plan pre-selection when navigated from other Streamlit pages, plus diff viewer for historical comparisons.

**Outstanding Enhancements**

- Collaborative review tooling (comments, approvals, change requests) and inline suggestions surfaced from the planning agent.
- Visual diff summarisation (highlights, bullet summaries) and printable/PDF exports for executive reviews.
- Automated regression checks before publishing a new version (linting, template adherence, required metadata fields).
- Plan template application and comparison (overlay templates to identify missing sections).

#### 3.4 Navigation Shell (`frontend/app.py`)

- Sidebar now links the new planning pages alongside existing chat/analytics experiences; add badges or notification dots once real-time updates land.
- Outstanding: consolidate global state (selected project/plan) into a shared store and surface a "Planning" landing page with quick links to active work.

#### 3.5 Feature Inventory & Outstanding Work

**Delivered Baseline (2025-09-30)**

- `frontend/pages/planning_chat.py` supports multi-session management, voice capture, automatic plan preview loading, and inline project provisioning.
- `frontend/pages/project_browser.py` offers search, filters, quick-open shortcuts into chat/viewer flows, and conversation listings per project.
- `frontend/pages/devplan_viewer.py` provides metadata editing, version history with unified diffs, markdown/JSON exports, and new-version workflows.

**Delivered UX Enhancements (2025-10-01)**

- ✅ Real-time refresh of chat transcripts, generated plans, and project stats: 10-second auto-polling with manual refresh
- ✅ Inline guidance for plan approvals: quick actions to mark plans approved/in-progress/completed/archived with visual feedback
- ✅ Project health widgets: health score, completion metrics, latest plan status chips with color coding
- ✅ Toast notifications for new plan generation and status updates
- ✅ Inline prompt scaffolding: 9 saved prompt templates across common planning scenarios
- ✅ Status visualization: Color-coded badges and chips for all plan and project statuses

**Outstanding UX Enhancements (required for Phase 3 sign-off)**

- Session timeline view (message + plan generation history) with voice playback of assistant responses using the TTS pipeline
- Accessibility & responsiveness audit for the Streamlit UI (keyboard navigation, screen reader labels, narrow viewport layouts)
- Rich notifications: email/Slack webhook integration when new plans or versions are generated (ties into monitoring stack)

**QA, Telemetry, and Definition of Done**

1. Add Streamlit/Playwright regression tests that cover plan generation, version diffing, and project navigation.
2. Extend telemetry to capture frontend usage metrics (page events, plan creation funnels) and emit them through the existing logging pipeline.
3. Document an end-to-end smoke script (`tests/e2e/test_planning_ui.py` placeholder) that provisions a project, generates a plan, edits metadata, and exports markdown.
4. Demo checklist: voice chat → plan generation → approval flow → project browser drill-down → version comparison without manual page refreshes.

### Phase 4: RAG Integration & Indexing (Week 4)

> **🚀 READY TO START - See `nextphase.md` for detailed implementation roadmap with 10 numbered steps.**

This phase implements semantic search and context retrieval using **Requesty embeddings API** with the embedding-001 model for creating and searching embeddings of projects, devplans, and conversations.

**Implementation Guide:** All Phase 4 tasks are documented in `nextphase.md` with:
- 10 numbered implementation steps
- Code examples and file references
- Testing strategies
- Progress tracking sections
- Handoff notes for continuation

#### 4.1 Devplan Indexing
**File**: `backend/devplan_processor.py`
```python
class DevPlanProcessor:
    """
    Process and index development plans into vector store.
    
    - Chunks plans into logical sections
    - Extracts metadata (project, phase, tasks)
    - Creates embeddings for semantic search using Requesty
    - Updates vector store
    """
    
    def process_plan(self, plan: DevPlan):
        """Process and index a single devplan."""
        
        # 1. Parse markdown into sections
        sections = self._parse_markdown(plan.content)
        
        # 2. Create documents with metadata
        documents = []
        for section in sections:
            doc = Document(
                page_content=section['content'],
                metadata={
                    "source": f"devplan_{plan.id}",
                    "project_id": plan.project_id,
                    "plan_title": plan.title,
                    "section": section['title'],
                    "version": plan.version,
                    "type": "devplan",
                    "created_at": plan.created_at
                }
            )
            documents.append(doc)
        
        # 3. Add to vector store using Requesty embeddings
        embeddings = requesty.embed([doc.page_content for doc in documents], model="embedding-001")
        self.vector_store.add_documents(documents, embeddings=embeddings)
        
        # 4. Update search index
        self._update_search_index(plan)
```

#### 4.2 Project Memory System
**File**: `backend/project_memory.py`
```python
class ProjectMemorySystem:
    """
    Maintains memory of all projects and their context.
    
    When user asks about a project or starts planning:
    - Retrieves project history
    - Gets related devplans
    - Finds similar past work using Requesty embeddings
    - Provides context to LLM
    """
    
    def get_project_context(self, project_id: str) -> dict:
        """Get comprehensive context for a project."""
        
        project = self.project_store.get(project_id)
        plans = self.plan_store.get_by_project(project_id)
        conversations = self.conversation_store.get_by_project(project_id)
        
        # Get similar projects using RAG with Requesty embeddings
        similar = self.rag.search(
            f"projects similar to {project.name}",
            filter={"type": "project"},
            k=3
        )
        
        return {
            "project": project,
            "plans": plans,
            "conversation_summary": self._summarize_conversations(conversations),
            "similar_projects": similar,
            "key_decisions": self._extract_key_decisions(plans),
            "lessons_learned": self._extract_lessons(conversations)
        }
```

#### 4.3 Auto-Indexing Pipeline
**File**: `backend/auto_indexer.py`
```python
"""
Automatically index new projects, plans, and conversations using Requesty embeddings.

Triggers:
- New project created → Index project metadata
- New devplan saved → Process and index plan
- Conversation completed → Summarize and index key points
- Plan updated → Re-index with new version
"""

class AutoIndexer:
    def __init__(self):
        self.plan_processor = DevPlanProcessor()
        self.project_indexer = ProjectIndexer()
        
    async def on_plan_created(self, plan: DevPlan):
        """Hook: Called when new plan is created."""
        await self.plan_processor.process_plan(plan)
        
    async def on_project_created(self, project: Project):
        """Hook: Called when new project is created."""
        await self.project_indexer.index_project(project)
        
    async def on_conversation_ended(self, session: ConversationSession):
        """Hook: Called when chat session ends."""
        summary = await self._summarize_session(session)
        await self._index_summary(summary)
```

### Phase 5: Voice Integration (Week 5)

Voice functionality combines **OpenAI Whisper for ASR** and **OpenAI TTS for speech output**, while conversation and plan generation continue to use Requesty APIs.

#### 5.1 Voice Planning Interface
**File**: `backend/voice_planner.py`
```python
class VoicePlanningService:
    """
    Specialized voice service for development planning.
    
    - Transcribes planning discussions using OpenAI Whisper
    - Handles technical terminology better
    - Generates structured plans from voice conversations using Requesty
    """
    
    async def process_planning_voice(
        self,
        audio: bytes,
        session_id: str,
        project_id: str = None
    ) -> dict:
        """
        Process voice input for planning conversation.
        
        Flow:
        1. Transcribe audio using OpenAI Whisper
        2. Send to planning agent (Requesty)
        3. Generate response (Requesty)
        4. Convert response to speech (OpenAI TTS)
        5. Detect if devplan should be created
        """
        
        # Transcribe using OpenAI Whisper
        transcript = await self.voice_service.transcribe(audio, model="whisper-1")
        
        # Get planning agent response via Requesty
        response, plan = await self.planning_agent.chat(
            transcript,
            session_id,
            project_id
        )
        
        # Convert to speech using OpenAI TTS
        audio_response = await self.voice_service.text_to_speech(response, model="gpt-4o-mini-tts")
        
        return {
            "transcript": transcript,
            "response": response,
            "audio": audio_response,
            "generated_plan": plan
        }
```

#### 5.2 Voice Commands
```python
# Special voice commands for planning
VOICE_COMMANDS = {
    "create new project": handle_create_project,
    "show my projects": handle_list_projects,
    "open project [name]": handle_open_project,
    "create devplan": handle_create_plan,
    "save this plan": handle_save_plan,
    "show version history": handle_show_versions,
}
```

### Phase 6: Advanced Features (Week 6)

Advanced features including templates, collaboration, and analytics are powered by Requesty for reasoning and plan updates.

#### 6.1 Plan Templates
**File**: `backend/plan_templates.py`
```python
"""
Pre-built templates for common development scenarios.

Templates:
- New Feature Development
- Bug Fix & Debugging
- Performance Optimization
- Security Enhancement
- Refactoring Project
- API Integration
- Database Migration
"""

TEMPLATES = {
    "new_feature": {
        "sections": ["Overview", "Requirements", "Design", "Implementation", "Testing"],
        "prompts": "Guide user through feature planning"
    },
    # ... more templates
}
```

#### 6.2 Collaborative Features
```python
# Share plans with team
POST /devplans/{id}/share
GET  /devplans/{id}/comments
POST /devplans/{id}/comments

# Export for project management tools
GET /devplans/{id}/export/jira
GET /devplans/{id}/export/trello
GET /devplans/{id}/export/github-issues
```

#### 6.3 Analytics & Insights
```python
# Planning analytics
GET /analytics/planning-metrics
    - Average plan completion time
    - Most common project types
    - Success rate of plans
    
GET /analytics/project-insights/{id}
    - Project velocity
    - Plan accuracy (estimates vs actuals)
    - Common blockers
```

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test each component
tests/unit/test_project_store.py
tests/unit/test_plan_store.py
tests/unit/test_planning_agent.py
tests/unit/test_plan_generator.py
tests/unit/test_devplan_processor.py
```

### Integration Tests
```bash
# Test end-to-end flows
tests/integration/test_create_project_flow.py
tests/integration/test_planning_conversation.py
tests/integration/test_plan_versioning.py
tests/integration/test_rag_integration.py
```

### Voice Tests
```bash
# Test voice planning
tests/voice/test_voice_planning.py
tests/voice/test_technical_terminology.py
```

## 📦 Database Migration

### Initial Schema
```sql
-- migrations/001_create_projects_table.sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    repository_path TEXT,
    tags JSON
);

-- migrations/002_create_devplans_table.sql
CREATE TABLE devplans (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    version INTEGER,
    title VARCHAR(255),
    content TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    metadata JSON
);

-- migrations/003_create_conversations_table.sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    messages JSON,
    summary TEXT
);
```

## 🚀 Deployment Checklist (API-Aware)

- [ ] Requesty API keys configured (chat + embeddings)
- [ ] OpenAI API keys configured (whisper + TTS only)
- [ ] `llm_client.py` abstraction implemented
- [ ] Database migrations applied
- [ ] Vector store updated with new indexes
- [ ] API endpoints tested
- [ ] Frontend pages deployed
- [ ] Voice integration tested
- [ ] RAG integration verified
- [ ] Monitoring added for new features
- [ ] Documentation updated
- [ ] User guide created
- [ ] Admin guide updated

## 📚 Documentation Updates

### User Documentation
- **Planning Guide**: How to use the planning feature
- **Voice Planning Tutorial**: Using voice for development planning
- **Project Management**: Organizing projects and plans
- **Collaboration**: Sharing and reviewing plans

### API Documentation
- Update OpenAPI spec with new endpoints
- Add examples for planning API
- Document request/response formats

### Admin Documentation
- Database schema documentation
- Backup and restore procedures for projects/plans
- Performance tuning for planning features

## 🎯 Success Metrics

### Feature Adoption
- Number of projects created
- Number of devplans generated
- Voice vs text usage ratio
- Average session length

### Quality Metrics
- Plan completion rate
- User satisfaction (feedback)
- Time to create devplan (before vs after)

### Technical Metrics
- RAG retrieval accuracy via Requesty embeddings
- LLM response quality from glm-4.5
- Whisper transcription accuracy
- TTS quality
- System performance (latency, throughput)

## 🔮 Future Enhancements

### Phase 7: AI Improvements
- Fine-tune Requesty models for devplan generation
- Improve context retrieval with semantic chunking
- Add multi-turn conversation handling
- Implement clarification questions

### Phase 8: Advanced Collaboration
- Real-time collaborative editing
- Team workspaces
- Role-based access control
- Plan approval workflows

### Phase 9: Integrations
- GitHub Issues sync
- Jira/Linear integration
- Slack notifications
- IDE plugins (VSCode extension)

### Phase 10: Intelligence
- Automatic task breakdown
- Effort estimation using ML
- Risk prediction
- Dependency detection

## 📝 Implementation Notes

### Key Design Decisions

1. **PostgreSQL for structured data**: Projects, plans, and conversations need relational data
2. **FAISS for plan search**: Leverage existing vector store for semantic search
3. **Hybrid storage**: Structured metadata in SQL, content in vector store
4. **Session-based chat**: Maintain context within sessions
5. **Markdown for plans**: Human-readable, version-control friendly
6. **Hybrid API approach**: Requesty for core functionality, OpenAI for voice

### Performance Considerations

- **Caching**: Cache frequently accessed projects and plans
- **Lazy loading**: Load plan content on-demand
- **Background indexing**: Index plans asynchronously using Requesty embeddings
- **Pagination**: Paginate project lists and version history

### Security Considerations

- **Access control**: Implement project-level permissions
- **Data encryption**: Encrypt sensitive project data
- **Audit logging**: Log all plan modifications
- **Rate limiting**: Prevent abuse of LLM APIs (both Requesty and OpenAI)

## Final API Split

- **Requesty** → devplan generation, project-aware chat, embeddings, RAG context, plan updates
- **OpenAI** → Whisper transcription + TTS

## 🎉 Conclusion

This implementation roadmap provides a comprehensive path to adding intelligent development planning capabilities to the voice-rag-system. The feature enables conversational planning, persistent memory, context-aware AI, voice support, version control, and searchable history.

**Estimated Timeline**: 6 weeks for MVP (Phases 1-5)  
**Team Size**: 1-2 developers  
**Key Technologies**: FastAPI, LangChain, PostgreSQL, FAISS, Streamlit, Requesty API, OpenAI API

*Ready to implement? Start with Phase 1: Core Data Layer & API, then switch to Requesty models at Phase 2 onward. Only use OpenAI for Whisper + TTS.*