# Development Planning Feature - Phase 1 Setup

This document captures the current implementation details and how to work with the newly added development planning backend. It complements `dev-planning-roadmap.md` by documenting what has been delivered so far and what remains.

> **Last updated:** 2025-09-30 — Phase 1 is now fully implemented and validated.

If you're picking up Phase 2 or later, start here, then review `PHASE1_QUICKSTART.md` for the end-to-end walkthrough and the roadmap for broader context.

## ✅ Delivered in Phase 1

- **Database layer**
  - Async SQLAlchemy models for `Project`, `DevPlan`, `DevPlanVersion`, `ConversationSession`, and `ConversationMessage`.
  - Engine configuration via `DATABASE_URL` (defaults to `sqlite+aiosqlite:///./data/devplanning.db`).
  - Startup/shutdown hooks initialise and dispose the database automatically.
  - Initial SQL migration scripts located under `backend/migrations/` for PostgreSQL deployments.

- **Storage layer**
  - `ProjectStore`, `DevPlanStore`, and `ConversationStore` provide CRUD operations and plan versioning helpers.

- **API layer**
  - `/projects` endpoints for managing planning projects.
  - `/devplans` endpoints for creating, updating, and exporting plans with version history.
  - `/planning` endpoints for chat session persistence (currently returning placeholder responses pending Phase 2).

- **Testing**
  - Unit tests validating stores and versioning logic using an in-memory SQLite database (`tests/unit/test_*_store.py`).

## ⚙️ Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string. Use `sqlite+aiosqlite:///./data/devplanning.db` for local dev or `postgresql+asyncpg://user:pass@host/db` in production. | `sqlite+aiosqlite:///./data/devplanning.db` |
| `DATABASE_ECHO` | Enables SQL echo for debugging when `true`. | `false` |
| `DATABASE_POOL_SIZE` | Core connection pool size. | `5` |
| `DATABASE_MAX_OVERFLOW` | Additional overflow connections allowed. | `10` |
| `ROUTER_API_KEY` | Requesty Router API key for planning + embeddings. Required for production agent behaviour. | _(empty)_ |
| `REQUESTY_PLANNING_MODEL` | Primary reasoning model routed through Requesty. | `requesty/glm-4.5` |
| `REQUESTY_EMBEDDING_MODEL` | Embedding model used for context retrieval hints. | `requesty/embedding-001` |
| `PLANNING_TEMPERATURE` | Temperature applied when generating agent responses. | `0.4` |
| `PLANNING_MAX_TOKENS` | Token budget for planning completions. | `2200` |

> **Note:** When switching to PostgreSQL, install `asyncpg` and update `DATABASE_URL` accordingly.

## 🧪 Testing the Planning Backend

```powershell
# Activate environment first if needed
pytest tests/unit/test_project_store.py -q
pytest tests/unit/test_plan_store.py -q
pytest tests/unit/test_conversation_store.py -q
```

The tests instantiate an in-memory SQLite database and verify basic CRUD + versioning behaviour.

## 🔗 Related References

- `PHASE1_QUICKSTART.md` — step-by-step execution guide that mirrors the automated setup.
- `dev-planning-roadmap.md` — multi-phase delivery plan with outstanding work tracked per phase.
- `PROJECT_STATUS.md` — high-level status board with current phase completion and next actions.

## 🚧 Open Items for Phase 2

- Expand agent analytics and telemetry once additional metrics are defined.
- Hook `/planning/generate` to the live agent pipeline (Phase 2.2).
- Extend test coverage to integration endpoints and async routers.

Track remaining work in `PROJECT_STATUS.md` (see the Development Planning Assistant expansion table).
