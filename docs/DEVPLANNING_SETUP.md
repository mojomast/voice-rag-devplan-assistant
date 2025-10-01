# Development Planning Feature – Phases 1 & 2 Setup

This guide summarises the delivered capabilities for the development planning stack (backend agent + Streamlit UI baseline) and how to run, configure, and test them. Consult `dev-planning-roadmap.md` for the in-progress Phase 3 backlog and future phases.

> **Last updated:** 2025-09-30 — Phases 1 & 2 are complete; Phase 3 frontend polish and collaboration tooling are underway.

## ✅ Delivered Capabilities

### Phase 1 — Data Layer & APIs

- **Database layer**: Async SQLAlchemy models (`Project`, `DevPlan`, `DevPlanVersion`, `ConversationSession`, `ConversationMessage`) with migrations and startup hooks.
- **Storage services**: `ProjectStore`, `DevPlanStore`, and `ConversationStore` wrap CRUD, plan versioning, and conversation summaries.
- **API surface**: `/projects`, `/devplans`, and `/planning` routers registered in `backend/main.py`, complete with pagination, filtering, and export helpers.
- **Foundational tests**: `tests/unit/test_*_store.py` cover async CRUD and versioning behaviour using in-memory SQLite.

### Phase 2 — Planning Agent & Requesty Integration

- **PlanningAgent pipeline**: Orchestrates conversations, context assembly, Requesty LLM calls (`requesty/glm-4.5`), and plan persistence.
- **DevPlanGenerator & ContextManager**: Convert agent actions into markdown plans, enrich prompts with project/plan history, and support deterministic TEST_MODE fallbacks.
- **API features**: `/planning/chat` now executes the full agent workflow, while `/planning/sessions` and `/planning/sessions/{id}` expose conversation history and generated plan IDs.
- **Telemetry & resilience**: Structured logging captures latency metrics, non-JSON fallbacks are handled gracefully, and Requesty/OpenAI API failures surface actionable errors.
- **Streamlit integration**: `frontend/pages/planning_chat.py`, `project_browser.py`, and `devplan_viewer.py` consume the live APIs for chat, browsing, and plan management workflows.
- **Test coverage**: 29 green tests across `tests/unit/test_planning_agent.py`, `tests/unit/test_plan_generator.py`, and `tests/integration/test_planning_chat.py` validate orchestration and Requesty integration.

## ⚙️ Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string. Use `sqlite+aiosqlite:///./data/devplanning.db` locally or `postgresql+asyncpg://user:pass@host/db` in production. | `sqlite+aiosqlite:///./data/devplanning.db` |
| `DATABASE_ECHO` | Enables SQL echo for debugging when `true`. | `false` |
| `DATABASE_POOL_SIZE` | Core connection pool size. | `5` |
| `DATABASE_MAX_OVERFLOW` | Additional overflow connections allowed. | `10` |
| `ROUTER_API_KEY` | Requesty Router API key for planning + embeddings. Required for production agent behaviour. | _(empty)_ |
| `REQUESTY_PLANNING_MODEL` | Primary reasoning model routed through Requesty. | `requesty/glm-4.5` |
| `REQUESTY_EMBEDDING_MODEL` | Embedding model used for context retrieval hints. | `requesty/embedding-001` |
| `PLANNING_TEMPERATURE` | Temperature applied when generating agent responses. | `0.4` |
| `PLANNING_MAX_TOKENS` | Token budget for planning completions. | `2200` |
| `TEST_MODE` | When `true`, uses deterministic stubs for Requesty/OpenAI and seeds a synthetic vector store. | `true` in `.env.example` |

> **Notes**
> - Install `asyncpg` when switching to PostgreSQL.
> - The Streamlit frontend reads the same `.env` file via `python-dotenv`; restart both backend and frontend after changing credentials.

## 🚀 Running the Planning Assistant

1. **Start the backend**
   ```powershell
   uvicorn backend.main:app --reload
   ```
2. **Launch the Streamlit interface**
   ```powershell
   streamlit run frontend/app.py
   ```
3. **Verify the planning agent**
   - Open http://localhost:8501 and navigate to **🗺️ Development Planning Assistant**.
   - Create a project, start a planning session, and send a sample prompt (e.g., "Help me design an onboarding flow").
   - A generated plan should appear in the sidebar; use **📋 DevPlan Viewer** to inspect versions and exports.

### API Smoke Test (optional)

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/planning/chat" -ContentType "application/json" -Body '{"message":"Draft a plan for adding analytics", "project_id":null}'
```

Expected response keys: `session_id`, `response`, and (when a plan is produced) `generated_plan_id`.

## 🧪 Testing

```powershell
# Core stores
pytest tests/unit/test_project_store.py -q
pytest tests/unit/test_plan_store.py -q
pytest tests/unit/test_conversation_store.py -q

# Planning agent pipeline
pytest tests/unit/test_planning_agent.py -q
pytest tests/unit/test_plan_generator.py -q

# API integration
pytest tests/integration/test_planning_chat.py -q
```

Enable `TEST_MODE=true` (default) to run the suite without real Requesty/OpenAI credentials. For manual smoke tests, point the Streamlit UI at the local backend and exercise chat → plan → version creation flows.

## 🔗 Related References

- `PHASE1_QUICKSTART.md` — historical walkthrough for Phase 1 scaffolding.
- `PHASE2_TEST_RESULTS.md` — detailed outcome of the 29 automated tests covering the agent pipeline.
- `dev-planning-roadmap.md` — canonical multi-phase roadmap with Phase 3 backlog details.
- `docs/USER_GUIDE.md` — end-user documentation (will gain planning updates alongside Phase 3).

## 🚧 Phase 3 Backlog Snapshot

- Real-time refresh for planning chat, generated plans, and project metrics (polling/websocket bridge).
- Approval workflow enhancements: quick actions for plan status changes, notifications, and review history.
- Accessibility & responsiveness improvements across planning pages, including keyboard navigation and focus management.
- Collaboration tooling: comment threads, plan templates, and saved prompt starters.
- Instrumentation & QA: Streamlit/Playwright regression path plus telemetry counters for key planning funnels.
