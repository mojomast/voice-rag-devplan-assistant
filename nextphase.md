# Phase 4: RAG Integration & Indexing — Implementation Roadmap

**Status:** Ready to Start  
**Created:** 2025-10-01  
**Phase:** Development Planning Assistant - Phase 4  
**Prerequisites:** Phases 1-3 Complete ✅

---

## 🎯 Phase 4 Objectives

Transform development plans and projects into searchable, semantically-indexed knowledge that enhances the planning agent's context awareness and enables intelligent retrieval of past work.

**Key Goals:**
1. Index all devplans and projects into the vector store
2. Enable semantic search across planning history
3. Provide planning agent with relevant context from past plans
4. Auto-index new plans as they're created
5. Support "related projects" and "similar plans" discovery

---

## 📋 Implementation Steps

### Step 1: Create DevPlan Processor for Vector Indexing
**Status:** ⏳ Not Started  
**Estimated Time:** 3-4 hours  
**Priority:** High  

**Tasks:**
- [ ] 1.1 Create `backend/devplan_processor.py` with `DevPlanProcessor` class
- [ ] 1.2 Implement `_parse_markdown()` method to chunk plan content into logical sections
- [ ] 1.3 Implement `process_plan()` method to create Document objects with metadata
- [ ] 1.4 Add `_extract_metadata()` to pull project_id, tags, status from plans
- [ ] 1.5 Integrate with Requesty `embedding-001` model for embeddings
- [ ] 1.6 Add `_update_search_index()` method for vector store updates

**Implementation Guide:**
```python
# File: backend/devplan_processor.py
from langchain.schema import Document
from typing import List, Dict
import re

class DevPlanProcessor:
    def __init__(self, vector_store, requesty_client):
        self.vector_store = vector_store
        self.requesty = requesty_client
    
    def _parse_markdown(self, content: str) -> List[Dict]:
        """Parse markdown into sections (## headings)."""
        # Split on ## headers, preserve title and content
        # Return list of {"title": str, "content": str, "order": int}
        pass
    
    def process_plan(self, plan: DevPlan) -> None:
        """Index a devplan into vector store."""
        # 1. Parse sections
        # 2. Create Document objects
        # 3. Generate embeddings with Requesty
        # 4. Add to vector store
        pass
```

**Files to Create/Modify:**
- Create: `backend/devplan_processor.py`
- Modify: `backend/auto_indexer.py` (add devplan processor integration)

**Testing:**
- Unit tests: `tests/unit/test_devplan_processor.py`
- Test markdown parsing with sample plans
- Verify embeddings are generated correctly

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 2: Create Project Memory System
**Status:** ⏳ Not Started  
**Estimated Time:** 3-4 hours  
**Priority:** High  

**Tasks:**
- [ ] 2.1 Create `backend/project_memory.py` with `ProjectMemorySystem` class
- [ ] 2.2 Implement `get_project_context()` to retrieve comprehensive project info
- [ ] 2.3 Add `find_similar_projects()` using vector similarity search
- [ ] 2.4 Implement `_extract_key_decisions()` from plan history
- [ ] 2.5 Add `_extract_lessons()` from conversation summaries
- [ ] 2.6 Create `get_related_plans()` for cross-project plan discovery

**Implementation Guide:**
```python
# File: backend/project_memory.py
from typing import Dict, List, Optional

class ProjectMemorySystem:
    def __init__(self, project_store, plan_store, conversation_store, rag_handler):
        self.project_store = project_store
        self.plan_store = plan_store
        self.conversation_store = conversation_store
        self.rag = rag_handler
    
    async def get_project_context(self, project_id: str) -> Dict:
        """Get comprehensive project context for planning."""
        # 1. Fetch project details
        # 2. Get all plans
        # 3. Get conversation history
        # 4. Find similar projects via RAG
        # 5. Extract key decisions and lessons
        return {
            "project": ...,
            "plans": ...,
            "similar_projects": ...,
            "key_decisions": ...,
            "lessons_learned": ...
        }
```

**Files to Create/Modify:**
- Create: `backend/project_memory.py`
- Modify: `backend/context_manager.py` (integrate project memory)

**Testing:**
- Unit tests: `tests/unit/test_project_memory.py`
- Integration tests: `tests/integration/test_project_context.py`
- Verify similar project retrieval accuracy

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 3: Update Auto-Indexer with DevPlan Processing
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** High  

**Tasks:**
- [ ] 3.1 Update `backend/auto_indexer.py` to instantiate `DevPlanProcessor`
- [ ] 3.2 Enhance `on_plan_created()` to call `process_plan()`
- [ ] 3.3 Add `on_plan_updated()` to re-index when plans change
- [ ] 3.4 Implement `on_plan_deleted()` to remove from vector store
- [ ] 3.5 Add `on_project_created()` to index project metadata
- [ ] 3.6 Create background task queue for async indexing (optional)

**Implementation Guide:**
```python
# File: backend/auto_indexer.py (modify existing)
from .devplan_processor import DevPlanProcessor
from .project_memory import ProjectMemorySystem

class AutoIndexer:
    def __init__(self):
        self.plan_processor = DevPlanProcessor(vector_store, requesty)
        self.project_memory = ProjectMemorySystem(...)
    
    async def on_plan_created(self, plan: DevPlan, content: str) -> None:
        """Hook: Index newly created plan."""
        await self.plan_processor.process_plan(plan)
        logger.info(f"Indexed plan {plan.id} into vector store")
    
    async def on_plan_updated(self, plan: DevPlan, content: str) -> None:
        """Hook: Re-index updated plan."""
        # Remove old entries, add new
        pass
```

**Files to Modify:**
- Modify: `backend/auto_indexer.py`
- Verify: `backend/routers/devplans.py` (already calls auto_indexer hooks)

**Testing:**
- Integration tests: `tests/integration/test_auto_indexing.py`
- Verify plans are indexed on creation
- Verify updates trigger re-indexing

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 4: Enhance Planning Agent Context with RAG
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** High  

**Tasks:**
- [ ] 4.1 Update `backend/context_manager.py` to use enhanced RAG queries
- [ ] 4.2 Implement semantic search for relevant past plans
- [ ] 4.3 Add "similar past work" section to planning prompts
- [ ] 4.4 Include related project lessons in context
- [ ] 4.5 Add configuration for RAG context limits (token budget)
- [ ] 4.6 Test context quality with real planning scenarios

**Implementation Guide:**
```python
# File: backend/context_manager.py (modify existing)
async def build_context(self, message: str, project_id: Optional[str]) -> Dict:
    """Build enhanced context with RAG-powered history."""
    context = await super().build_context(message, project_id)
    
    # Add semantic search results
    if self.rag_handler:
        similar_plans = await self.rag_handler.search(
            query=message,
            filter={"type": "devplan", "project_id": project_id},
            k=3
        )
        context["similar_past_work"] = similar_plans
    
    return context
```

**Files to Modify:**
- Modify: `backend/context_manager.py`
- Modify: `backend/planning_agent.py` (use enhanced context)

**Testing:**
- Integration tests: `tests/integration/test_enhanced_context.py`
- Verify similar plans are retrieved correctly
- Test token budget limits

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 5: Add Semantic Search API Endpoints
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** Medium  

**Tasks:**
- [ ] 5.1 Create `backend/routers/search.py` for search endpoints
- [ ] 5.2 Add `POST /search/plans` for semantic plan search
- [ ] 5.3 Add `POST /search/projects` for semantic project search
- [ ] 5.4 Add `GET /search/related/{plan_id}` for related plans
- [ ] 5.5 Add `GET /search/similar-projects/{project_id}` endpoint
- [ ] 5.6 Include filters (date range, status, tags) in search

**Implementation Guide:**
```python
# File: backend/routers/search.py (create new)
from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/plans")
async def search_plans(
    query: str,
    project_id: Optional[str] = None,
    status: Optional[List[str]] = None,
    limit: int = Query(10, le=50)
):
    """Semantic search across development plans."""
    # Use RAG handler to search vector store
    # Filter by project_id, status, etc.
    # Return ranked results with snippets
    pass
```

**Files to Create:**
- Create: `backend/routers/search.py`
- Modify: `backend/main.py` (register search router)

**Testing:**
- Integration tests: `tests/integration/test_search_api.py`
- Test various search queries
- Verify filtering works correctly

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 6: Add "Related Projects" UI Component
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** Medium  

**Tasks:**
- [ ] 6.1 Update `frontend/pages/project_browser.py` with related projects sidebar
- [ ] 6.2 Add `_fetch_related_projects()` API call function
- [ ] 6.3 Display related projects with similarity scores
- [ ] 6.4 Add click-to-navigate functionality
- [ ] 6.5 Show key insights from related projects
- [ ] 6.6 Add telemetry for related project clicks

**Implementation Guide:**
```python
# In frontend/pages/project_browser.py
def _fetch_related_projects(project_id: str) -> List[Dict]:
    """Fetch semantically similar projects."""
    response, error = api_request("GET", f"/search/similar-projects/{project_id}")
    if response and response.status_code == 200:
        return parse_response_json(response) or []
    return []

# In project details section:
st.markdown("### 🔗 Related Projects")
related = _fetch_related_projects(project_id)
for proj in related:
    with st.expander(f"{proj['name']} (Similarity: {proj['score']:.0%})"):
        st.write(proj['description'])
        if st.button("View Project", key=f"related_{proj['id']}"):
            st.session_state["project_browser.selected_project_id"] = proj["id"]
            st.rerun()
```

**Files to Modify:**
- Modify: `frontend/pages/project_browser.py`
- Modify: `frontend/pages/planning_chat.py` (optional: show related plans)

**Testing:**
- Manual UI testing
- Verify API integration works
- Test with various projects

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 7: Create Bulk Re-Indexing Script
**Status:** ⏳ Not Started  
**Estimated Time:** 2 hours  
**Priority:** Medium  

**Tasks:**
- [ ] 7.1 Create `backend/scripts/reindex_all.py` script
- [ ] 7.2 Implement batch processing of all existing plans
- [ ] 7.3 Add progress bar and logging
- [ ] 7.4 Include error handling and retry logic
- [ ] 7.5 Add dry-run mode for testing
- [ ] 7.6 Document usage in README or admin guide

**Implementation Guide:**
```python
# File: backend/scripts/reindex_all.py
"""
Bulk re-indexing script for all development plans.

Usage:
    python -m backend.scripts.reindex_all --dry-run
    python -m backend.scripts.reindex_all --batch-size 10
"""
import asyncio
from tqdm import tqdm

async def reindex_all_plans(batch_size=10, dry_run=False):
    # 1. Fetch all plans from database
    # 2. Process in batches
    # 3. Index each plan
    # 4. Log progress
    pass

if __name__ == "__main__":
    asyncio.run(reindex_all_plans())
```

**Files to Create:**
- Create: `backend/scripts/reindex_all.py`
- Create: `backend/scripts/__init__.py`

**Testing:**
- Test with dry-run mode
- Verify indexing completes without errors
- Check vector store contains indexed plans

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 8: Add Search UI to Planning Chat
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** Low  

**Tasks:**
- [ ] 8.1 Add search box to `frontend/pages/planning_chat.py`
- [ ] 8.2 Display search results in sidebar or expander
- [ ] 8.3 Allow clicking search results to view plans
- [ ] 8.4 Add "Use as context" button to insert past plan into conversation
- [ ] 8.5 Show search history (recent searches)
- [ ] 8.6 Add telemetry for search usage

**Implementation Guide:**
```python
# In frontend/pages/planning_chat.py
with st.sidebar:
    st.markdown("### 🔍 Search Past Plans")
    search_query = st.text_input("Search", placeholder="semantic search...")
    
    if search_query:
        response, _ = api_request("POST", "/search/plans", json={"query": search_query, "limit": 5})
        if response and response.status_code == 200:
            results = parse_response_json(response) or []
            for result in results:
                with st.expander(f"{result['title']} ({result['score']:.0%})"):
                    st.caption(result['snippet'])
                    if st.button("View Plan", key=f"search_{result['id']}"):
                        st.session_state["devplan_viewer.selected_plan_id"] = result["id"]
                        _toast("Plan selected for viewing", icon="🔍")
```

**Files to Modify:**
- Modify: `frontend/pages/planning_chat.py`

**Testing:**
- Manual UI testing
- Test search functionality
- Verify result clicking works

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 9: Update Documentation
**Status:** ⏳ Not Started  
**Estimated Time:** 1-2 hours  
**Priority:** High  

**Tasks:**
- [ ] 9.1 Update `README.md` with Phase 4 completion status
- [ ] 9.2 Update `dev-planning-roadmap.md` to mark Phase 4 complete
- [ ] 9.3 Add RAG integration documentation to `docs/DEVPLANNING_SETUP.md`
- [ ] 9.4 Document search API in `docs/API.md` (create if needed)
- [ ] 9.5 Update `PHASE3_PROGRESS.md` → `PHASE4_PROGRESS.md`
- [ ] 9.6 Create usage examples for semantic search

**Files to Update:**
- Update: `README.md`
- Update: `dev-planning-roadmap.md`
- Update: `docs/DEVPLANNING_SETUP.md`
- Create: `docs/API.md` (if needed)
- Update: Create `PHASE4_PROGRESS.md`

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

### Step 10: Testing & Validation
**Status:** ⏳ Not Started  
**Estimated Time:** 2-3 hours  
**Priority:** High  

**Tasks:**
- [ ] 10.1 Run bulk re-indexing on existing plans
- [ ] 10.2 Test semantic search quality with various queries
- [ ] 10.3 Verify planning agent uses RAG context correctly
- [ ] 10.4 Test related projects discovery accuracy
- [ ] 10.5 Run full test suite (unit + integration + E2E)
- [ ] 10.6 Performance test vector search with large plan corpus

**Testing Checklist:**
- [ ] Index 10+ sample plans
- [ ] Search for various planning concepts
- [ ] Verify relevant plans are returned
- [ ] Test with edge cases (empty plans, long plans)
- [ ] Measure search latency (<500ms)
- [ ] Verify auto-indexing on new plan creation

**Progress Notes:**
```
[Agent: Add your progress notes here as you work]
- 
```

---

## 📊 Progress Tracking

| Step | Feature | Status | Time Spent | Completion % |
|------|---------|--------|------------|--------------|
| 1 | DevPlan Processor | ⏳ Not Started | 0h | 0% |
| 2 | Project Memory System | ⏳ Not Started | 0h | 0% |
| 3 | Auto-Indexer Updates | ⏳ Not Started | 0h | 0% |
| 4 | Enhanced Agent Context | ⏳ Not Started | 0h | 0% |
| 5 | Search API Endpoints | ⏳ Not Started | 0h | 0% |
| 6 | Related Projects UI | ⏳ Not Started | 0h | 0% |
| 7 | Bulk Re-indexing Script | ⏳ Not Started | 0h | 0% |
| 8 | Search UI | ⏳ Not Started | 0h | 0% |
| 9 | Documentation Updates | ⏳ Not Started | 0h | 0% |
| 10 | Testing & Validation | ⏳ Not Started | 0h | 0% |

**Overall Phase 4 Completion: 0%**

---

## 🧪 Testing Strategy

### Unit Tests Required
- `tests/unit/test_devplan_processor.py` - Markdown parsing, document creation
- `tests/unit/test_project_memory.py` - Context retrieval, similarity search
- `tests/unit/test_search_api.py` - Search endpoint logic

### Integration Tests Required
- `tests/integration/test_auto_indexing.py` - End-to-end indexing flow
- `tests/integration/test_enhanced_context.py` - RAG-enhanced planning
- `tests/integration/test_search_flow.py` - Full search workflow

### Performance Tests
- Vector search latency (<500ms)
- Bulk indexing throughput (>10 plans/sec)
- Context retrieval speed (<200ms)

---

## 🎯 Success Criteria

Phase 4 is considered complete when:

- [x] All 10 implementation steps are marked complete
- [ ] DevPlans are automatically indexed on creation
- [ ] Semantic search returns relevant results
- [ ] Planning agent uses RAG context effectively
- [ ] Related projects feature works in UI
- [ ] Bulk re-indexing script is operational
- [ ] All tests pass (unit + integration)
- [ ] Documentation is updated
- [ ] Performance meets targets

---

## 📚 Reference Documentation

**Key Files to Understand:**
- `backend/rag_handler.py` - Existing RAG implementation
- `backend/auto_indexer.py` - Current auto-indexer (basic)
- `backend/context_manager.py` - Planning context builder
- `backend/planning_agent.py` - Agent orchestration

**API Patterns to Follow:**
- Use async/await throughout
- Follow existing router patterns in `backend/routers/`
- Use Pydantic models for request/response validation
- Include error handling and logging

**Testing Patterns:**
- See `tests/unit/test_planning_agent.py` for unit test examples
- See `tests/integration/test_planning_chat.py` for integration patterns
- Use pytest fixtures for database setup/teardown

---

## 🔧 Development Setup

**Prerequisites:**
1. Phases 1-3 must be complete
2. Vector store initialized (FAISS or equivalent)
3. Requesty API credentials configured
4. Database with sample plans for testing

**Start Development:**
```bash
# Activate environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start backend
uvicorn backend.main:app --reload

# In another terminal, start frontend
streamlit run frontend/app.py

# Run tests as you develop
pytest tests/unit/test_devplan_processor.py -v
```

---

## 💡 Implementation Tips

1. **Start Simple:** Begin with Step 1 (DevPlan Processor) as it's foundational
2. **Test Incrementally:** Write tests as you implement each feature
3. **Use Existing Patterns:** Follow code patterns from Phases 1-3
4. **Check Auto-Indexer:** The auto-indexer already has hooks; just fill them in
5. **RAG Handler Exists:** `backend/rag_handler.py` already has vector store logic
6. **Requesty Integration:** Use `requesty/embedding-001` for embeddings
7. **Mock for Tests:** Use TEST_MODE to avoid external API calls in tests

---

## 🚀 Next Phase Preview

**Phase 5: Voice-First Planning & Advanced Collaboration**

After completing Phase 4, the next focus areas will be:
1. Voice command support for planning actions
2. TTS playback of planning agent responses
3. Session timeline visualization with audio
4. Multi-user collaboration features
5. Real-time plan co-editing
6. Webhook notifications (Email/Slack)
7. Advanced analytics and insights

---

## 📝 Notes for Future Agent

**Context for Continuation:**
- Phase 3 is 100% complete with production-ready UI
- All backend infrastructure is in place
- RAG handler exists but isn't used for plan indexing yet
- Auto-indexer has hooks but needs implementation
- Focus on Step 1 first - it's the foundation

**Common Pitfalls to Avoid:**
- Don't duplicate RAG logic - reuse `rag_handler.py`
- Remember to use async/await consistently
- Always add error handling for vector store operations
- Test with real markdown content, not just simple strings
- Consider token limits when building context

**Questions to Ask User:**
1. Should we use FAISS, Pinecone, or another vector store?
2. What's the token budget for context (default 2000 tokens)?
3. Should search be project-scoped by default?
4. Do we need to index conversation content (not just plans)?

---

**Last Updated:** 2025-10-01  
**Phase Status:** Ready to Start  
**Est. Total Time:** 20-25 hours  
**Recommended Timeline:** 1-2 weeks

---

*This file should be updated as work progresses. Mark steps complete, add notes, and update progress percentages.*
