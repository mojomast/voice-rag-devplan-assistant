# Phase 4: Testing & Validation Guide

**Status:** Ready for Testing  
**Date:** 2025-10-01  
**Prerequisites:** All implementation complete (Steps 1-9)

---

## Overview

This guide provides a comprehensive testing plan to validate Phase 4 RAG integration functionality before marking the phase complete.

---

## Pre-Test Checklist

### 1. Environment Setup

```bash
# Ensure backend is running
uvicorn backend.main:app --reload

# Verify Requesty API key is set
# In .env:
# ROUTER_API_KEY=your-key-here
```

### 2. Database State

```bash
# Check if you have test data
sqlite3 data/devplanning.db "SELECT COUNT(*) FROM devplans;"
sqlite3 data/devplanning.db "SELECT COUNT(*) FROM projects;"
```

**If no data exists**, create sample projects and plans through the UI first.

### 3. Vector Store Initialization

```bash
# Run bulk re-indexing (dry run first)
python -m backend.scripts.reindex_all --dry-run

# If looks good, run actual indexing
python -m backend.scripts.reindex_all

# Expected output:
# ============================================================
# Re-indexing Complete
# ============================================================
# Plans:         X/X indexed (0 failed)
# Projects:      X/X indexed (0 failed)
# Conversations: X/X indexed (0 failed)
# ============================================================
```

---

## Testing Checklist

### ✅ Step 1: DevPlan Processor

**What to Test:** Markdown parsing and chunking

**Test Steps:**
1. Create a new development plan with multiple sections
2. Check logs for indexing confirmation
3. Verify vector store files exist

**Commands:**
```bash
# Check vector store was created
ls -la vector_store/devplans/

# Should see:
# index.faiss
# index.pkl
```

**Success Criteria:**
- [ ] Plan created without errors
- [ ] Logs show "Indexed development plan" message
- [ ] Vector store files present
- [ ] File sizes > 0 bytes

---

### ✅ Step 2: Project Memory System

**What to Test:** Context aggregation and similarity search

**Test Steps:**
1. Access a project with multiple plans
2. Start a planning conversation
3. Check if similar projects are suggested

**Backend Test:**
```python
# In Python console or test script
from backend.project_memory import ProjectMemorySystem
from backend.database import get_async_session_context
from backend.storage.project_store import ProjectStore
from backend.storage.plan_store import DevPlanStore
from backend.storage.conversation_store import ConversationStore
from backend.rag_handler import RAGHandler

async def test_memory():
    async with get_async_session_context() as session:
        memory = ProjectMemorySystem(
            project_store=ProjectStore(session),
            plan_store=DevPlanStore(session),
            conversation_store=ConversationStore(session),
            rag_handler=RAGHandler()
        )
        
        # Replace with actual project ID
        context = await memory.get_project_context("project-id-here")
        print(f"Similar projects: {len(context['similar_projects'])}")
        print(f"Key decisions: {len(context['key_decisions'])}")
        print(f"Lessons learned: {len(context['lessons_learned'])}")

import asyncio
asyncio.run(test_memory())
```

**Success Criteria:**
- [ ] Function executes without errors
- [ ] Returns similar projects (if >1 project exists)
- [ ] Extracts key decisions from plans
- [ ] Context object well-formed

---

### ✅ Step 3: Auto-Indexer

**What to Test:** Event-driven indexing on CRUD operations

**Test Steps:**

1. **Create Plan:**
   - Go to Planning Chat
   - Generate a new plan
   - Check logs for "Indexed development plan" message

2. **Update Plan:**
   - Edit an existing plan (change title or status)
   - Check logs for re-indexing message

3. **Delete Plan:**
   - Delete a test plan
   - Check logs for "Removed plan X from vector index"

**Log Monitoring:**
```bash
# Watch logs in real-time
tail -f logs/app.log | grep -i "index"
```

**Success Criteria:**
- [ ] New plans trigger `on_plan_created`
- [ ] Updates trigger `on_plan_updated`
- [ ] Deletes trigger `on_plan_deleted`
- [ ] No errors in logs
- [ ] Vector store stays in sync

---

### ✅ Step 4: Enhanced Planning Agent Context

**What to Test:** RAG-enhanced prompts to planning agent

**Test Steps:**
1. Start a planning conversation
2. Ask: "Design an authentication system"
3. Observe if agent references similar past work

**Expected Behavior:**
- Agent should mention similar plans if they exist
- Context should include project history
- Suggestions should be relevant

**Manual Check:**
Review the agent's response for phrases like:
- "Based on similar projects..."
- "In past work, we found..."
- "Related plans show..."

**Success Criteria:**
- [ ] Agent uses enriched context
- [ ] Mentions similar past work
- [ ] Provides relevant suggestions
- [ ] No context errors in logs

---

### ✅ Step 5: Search API Endpoints

**What to Test:** All 4 search endpoints

#### Test 1: Search Plans
```bash
curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "limit": 5
  }' | jq
```

**Expected Response:**
```json
{
  "results": [
    {
      "id": "plan-xxx",
      "title": "...",
      "type": "devplan",
      "score": 0.85,
      "content_preview": "..."
    }
  ],
  "query": "authentication",
  "total_found": 1
}
```

#### Test 2: Search Projects
```bash
curl -X POST http://localhost:8000/search/projects \
  -H "Content-Type: application/json" \
  -d '{
    "query": "microservices",
    "limit": 3
  }' | jq
```

#### Test 3: Related Plans
```bash
# Replace plan-123 with actual plan ID
curl http://localhost:8000/search/related-plans/plan-123?limit=5 | jq
```

#### Test 4: Similar Projects
```bash
# Replace proj-123 with actual project ID
curl http://localhost:8000/search/similar-projects/proj-123?limit=5 | jq
```

**Success Criteria:**
- [ ] All 4 endpoints return 200 OK
- [ ] Results contain expected fields
- [ ] Scores are between 0.0 and 1.0
- [ ] Content previews are meaningful
- [ ] No 500 errors

---

### ✅ Step 6: Related Projects UI

**What to Test:** Related projects sidebar in project browser

**Test Steps:**
1. Open Project Browser: `http://localhost:8501` → `📁 Project Browser`
2. Select a project
3. Scroll to "🔗 Related Projects" section

**Expected Display:**
- Section titled "🔗 Related Projects"
- Caption: "Semantically similar projects found via RAG analysis"
- List of similar projects with similarity scores
- "View This Project" buttons

**Interactive Test:**
- Click "View This Project" on a related project
- Should navigate to that project
- Toast notification should appear

**Success Criteria:**
- [ ] Related Projects section visible
- [ ] Shows similarity scores (e.g., 78%)
- [ ] Lists project metadata (tags, plan count)
- [ ] "View This Project" button works
- [ ] No UI errors or blank sections

---

### ✅ Step 7: Bulk Re-indexing Script

**What to Test:** Script functionality and options

#### Test 1: Dry Run
```bash
python -m backend.scripts.reindex_all --dry-run
```

**Expected:**
- Shows what would be indexed
- No actual changes made
- Progress bar completes
- Summary statistics displayed

#### Test 2: Plans Only
```bash
python -m backend.scripts.reindex_all --plans-only
```

**Expected:**
- Only processes plans
- Projects and conversations skipped
- Completes successfully

#### Test 3: Full Re-index
```bash
python -m backend.scripts.reindex_all
```

**Expected:**
- Indexes all plans, projects, conversations
- Progress bars for each category
- Final summary with statistics
- No errors

**Success Criteria:**
- [ ] Dry run works without errors
- [ ] Selective indexing (--plans-only) works
- [ ] Full re-index completes successfully
- [ ] Progress bars show real-time status
- [ ] Statistics are accurate

---

### ✅ Step 8: Search UI in Planning Chat

**What to Test:** Semantic search sidebar

**Test Steps:**
1. Open Planning Chat: `http://localhost:8501` → `🗺️ Development Planning Assistant`
2. Look for sidebar on the left
3. See "🔍 Search Past Plans" section

**Functional Tests:**

**Test 1: Basic Search**
1. Enter query: "authentication system"
2. Select "All Projects"
3. Click "🔍 Search"

**Expected:**
- Spinner appears during search
- Results show with similarity scores
- Each result has preview text
- "View Full Plan" and "Use as Context" buttons present

**Test 2: Scoped Search**
1. Select a project from dropdown
2. Enter query: "database"
3. Select "Current Project"
4. Click "🔍 Search"

**Expected:**
- Only returns results from current project
- Works correctly

**Test 3: View Full Plan**
1. Search for a plan
2. Click "View Full Plan"

**Expected:**
- Plan appears in "Latest Generated Plans" section
- Toast notification shows

**Test 4: Use as Context**
1. Search for a plan
2. Click "Use as Context"

**Expected:**
- Message added to conversation
- Chat continues with plan as context

**Success Criteria:**
- [ ] Sidebar visible and styled correctly
- [ ] Search executes and returns results
- [ ] Similarity scores displayed (e.g., 85%)
- [ ] Preview text shows relevant content
- [ ] "View Full Plan" adds plan to view
- [ ] "Use as Context" adds to conversation
- [ ] No JavaScript errors in console

---

### ✅ Step 9: Documentation

**What to Test:** Documentation completeness and accuracy

**Review Checklist:**

#### README.md
- [ ] Phase 4 status updated to 90%
- [ ] Lists key RAG features
- [ ] Mentions search API
- [ ] Links to detailed docs

#### API_SEARCH.md
- [ ] All 4 endpoints documented
- [ ] Request/response examples provided
- [ ] Error scenarios covered
- [ ] Code examples for Python/JS/cURL
- [ ] Troubleshooting section included

#### RAG_INTEGRATION.md
- [ ] Architecture explained with diagrams
- [ ] How indexing works described
- [ ] Vector store structure documented
- [ ] Performance optimization tips included
- [ ] Best practices listed
- [ ] Troubleshooting guide complete

#### PHASE4_PROGRESS.md
- [ ] All steps documented
- [ ] Progress accurately reflected
- [ ] Implementation notes detailed
- [ ] Files created/modified listed

**Success Criteria:**
- [ ] All documentation reads clearly
- [ ] No broken links or references
- [ ] Code examples are accurate
- [ ] API examples work when tested
- [ ] Troubleshooting scenarios cover common issues

---

### ⏳ Step 10: Integration Testing

**What to Test:** End-to-end user workflows

#### Workflow 1: Create Project → Plan → Search

1. **Create Project:**
   - Name: "E-commerce API"
   - Description: "RESTful API for online shopping"
   - Tags: "API", "e-commerce", "REST"

2. **Generate Plan:**
   - Go to Planning Chat
   - Ask: "Design a product catalog API"
   - Wait for plan generation

3. **Search for Plan:**
   - Use semantic search: "product catalog"
   - Verify plan appears in results
   - Check similarity score

4. **Find Related Projects:**
   - View project in Project Browser
   - Check "Related Projects" section
   - Should show similar projects (if any exist)

**Expected Result:**
- Plan is automatically indexed after creation
- Search finds the plan with high score (>0.7)
- Related projects appear (if applicable)

#### Workflow 2: Multi-Project Context

1. **Create Multiple Projects:**
   - Project A: "User Authentication Service"
   - Project B: "API Gateway"
   - Project C: "Payment Processing"

2. **Generate Plans:**
   - Create 1-2 plans per project
   - Use varied terminology

3. **Test Cross-Project Search:**
   - Search: "authentication"
   - Should find plans from Project A
   - Search: "gateway"
   - Should find plans from Project B

4. **Test Similar Projects:**
   - View Project B (API Gateway)
   - Check if Project A or C appear as similar
   - Verify similarity makes sense

**Success Criteria:**
- [ ] Plans searchable immediately after creation
- [ ] Search works across all projects
- [ ] Similar projects detection works
- [ ] Scores reflect actual relevance
- [ ] UI responsive and bug-free

---

## Performance Testing

### Response Time Benchmarks

**Target Metrics:**
- Search API: < 500ms per query
- Indexing: < 1s per plan
- Re-indexing: > 10 plans/second

**Test Commands:**

```bash
# Measure search latency
time curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":10}'

# Should complete in < 0.5 seconds
```

**Success Criteria:**
- [ ] Search responds in < 500ms (warm)
- [ ] Plan indexing completes in < 1s
- [ ] Bulk re-indexing > 10 plans/sec
- [ ] UI remains responsive during searches

---

## Edge Case Testing

### Test 1: Empty Query
```bash
curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{"query":"","limit":5}'
```

**Expected:** Should handle gracefully, return empty or all results

### Test 2: Very Long Query
```bash
curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{
    "query":"'$(python -c 'print("a" * 10000)')'",
    "limit":5
  }'
```

**Expected:** Should not crash, may truncate or handle appropriately

### Test 3: No Index Exists
```bash
# Temporarily rename vector store
mv vector_store vector_store.backup
curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":5}'
# Restore
mv vector_store.backup vector_store
```

**Expected:** Graceful error message, no crash

### Test 4: Non-existent Plan ID
```bash
curl http://localhost:8000/search/related-plans/nonexistent-plan-id
```

**Expected:** 404 Not Found with clear error message

**Success Criteria:**
- [ ] Handles empty queries
- [ ] Handles very long queries
- [ ] Returns clear errors when index missing
- [ ] Returns 404 for invalid IDs
- [ ] No server crashes

---

## Final Checklist

### Functional Requirements
- [ ] All plans automatically indexed on creation
- [ ] Plans re-indexed on updates
- [ ] Plans removed from index on deletion
- [ ] Semantic search returns relevant results
- [ ] Related plans discovery works
- [ ] Similar projects discovery works
- [ ] Planning agent uses RAG context
- [ ] Search UI functional in planning chat
- [ ] Related projects UI functional in browser

### Non-Functional Requirements
- [ ] Search response time < 500ms
- [ ] Bulk indexing > 10 plans/second
- [ ] No memory leaks during indexing
- [ ] Vector stores persist across restarts
- [ ] Logs are informative and error-free

### Documentation
- [ ] README updated
- [ ] API docs complete and accurate
- [ ] RAG integration guide comprehensive
- [ ] Progress tracking up to date
- [ ] All code examples tested

### User Experience
- [ ] UI elements styled consistently
- [ ] Loading states show progress
- [ ] Error messages are helpful
- [ ] Toast notifications informative
- [ ] No broken buttons or links

---

## Sign-off

When all tests pass:

1. **Mark Step 10 Complete** in `nextphase.md`
2. **Update PHASE4_PROGRESS.md** to 100%
3. **Update README.md** to reflect Phase 4 completion
4. **Create Git commit** with all changes
5. **Celebrate!** 🎉 Phase 4 is complete!

---

**Testing Started:** [Date]  
**Testing Completed:** [Date]  
**Issues Found:** [Count]  
**All Issues Resolved:** [ ] Yes / [ ] No

**Tester Signature:** ___________________  
**Date:** ___________________

---

## Appendix: Common Issues & Solutions

### Issue: "Vector store not found"
**Solution:** Run `python -m backend.scripts.reindex_all`

### Issue: "No search results"
**Solution:** Check if plans exist and are indexed

### Issue: "Slow search performance"
**Solution:** Add project filters or reduce result limit

### Issue: "Indexing fails"
**Solution:** Verify ROUTER_API_KEY in `.env`, check network

### Issue: "Related projects not showing"
**Solution:** Need at least 2 projects with different descriptions

For more troubleshooting, see `docs/RAG_INTEGRATION.md`.
