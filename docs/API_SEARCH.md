# Search API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:8000` (development)  
**Endpoints Prefix:** `/search`

---

## Overview

The Search API provides semantic search capabilities across development plans and projects using RAG (Retrieval-Augmented Generation) with vector embeddings. All searches are powered by the Requesty `embedding-001` model and FAISS vector stores.

### Key Features
- **Semantic Understanding**: Searches understand concepts, not just keywords
- **Relevance Ranking**: Results scored by similarity (0.0 to 1.0)
- **Metadata Filtering**: Filter by project, status, tags, etc.
- **Related Item Discovery**: Find similar plans and projects automatically
- **Fast Performance**: Sub-500ms response times for most queries

---

## Authentication

Currently, the Search API does not require authentication for local development. For production deployments, implement the same authentication scheme used by other API endpoints.

---

## Endpoints

### 1. Search Plans

**Endpoint:** `POST /search/plans`

**Description:** Perform semantic search across all development plans.

**Request Body:**
```json
{
  "query": "authentication implementation with JWT",
  "project_id": "proj-123",
  "status": ["in_progress", "completed"],
  "limit": 10
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (natural language) |
| `project_id` | string | No | Filter by specific project ID |
| `status` | array[string] | No | Filter by plan status(es) |
| `limit` | integer | No | Max results (1-50, default: 10) |

**Response:**
```json
{
  "results": [
    {
      "id": "plan-456",
      "title": "User Authentication System",
      "type": "devplan",
      "content_preview": "## Authentication Flow\nImplement JWT-based authentication with refresh tokens...",
      "score": 0.89,
      "metadata": {
        "project_id": "proj-123",
        "status": "in_progress",
        "section_title": "Authentication Flow",
        "version": 2,
        "updated_at": "2025-10-01T12:34:56"
      }
    }
  ],
  "query": "authentication implementation with JWT",
  "total_found": 1
}
```

**Score Interpretation:**
- `0.9 - 1.0`: Highly relevant
- `0.7 - 0.9`: Very relevant
- `0.5 - 0.7`: Moderately relevant
- `< 0.5`: Low relevance

**Example cURL:**
```bash
curl -X POST http://localhost:8000/search/plans \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database migration strategy",
    "limit": 5
  }'
```

**Status Codes:**
- `200 OK`: Successful search
- `500 Internal Server Error`: Search failed

---

### 2. Search Projects

**Endpoint:** `POST /search/projects`

**Description:** Perform semantic search across all projects.

**Request Body:**
```json
{
  "query": "microservices architecture",
  "limit": 5
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (natural language) |
| `limit` | integer | No | Max results (1-50, default: 10) |

**Response:**
```json
{
  "results": [
    {
      "id": "proj-789",
      "title": "Payment Gateway Service",
      "type": "project",
      "content_preview": "Project: Payment Gateway Service\nStatus: active\nTags: microservices, payments, API...",
      "score": 0.82,
      "metadata": {
        "status": "active",
        "tags": ["microservices", "payments", "API"],
        "plan_count": 12,
        "conversation_count": 5,
        "updated_at": "2025-09-30T08:15:22"
      }
    }
  ],
  "query": "microservices architecture",
  "total_found": 1
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/search/projects \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning pipeline",
    "limit": 3
  }'
```

---

### 3. Get Related Plans

**Endpoint:** `GET /search/related-plans/{plan_id}`

**Description:** Find development plans semantically related to a specific plan.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan_id` | string | Yes | ID of the source plan |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Max results (1-20, default: 5) |

**Response:**
```json
[
  {
    "id": "plan-999",
    "title": "OAuth2 Integration",
    "similarity_score": 0.76,
    "type": "devplan",
    "metadata": {
      "project_id": "proj-456",
      "status": "completed",
      "version": 1
    }
  }
]
```

**Example cURL:**
```bash
curl http://localhost:8000/search/related-plans/plan-123?limit=5
```

**Status Codes:**
- `200 OK`: Successfully retrieved related plans
- `404 Not Found`: Source plan not found
- `500 Internal Server Error`: Search failed

**Use Cases:**
- "Show me similar plans for reference"
- "What other plans dealt with authentication?"
- "Find related work across projects"

---

### 4. Get Similar Projects

**Endpoint:** `GET /search/similar-projects/{project_id}`

**Description:** Find projects semantically similar to a specific project.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | ID of the source project |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Max results (1-20, default: 5) |

**Response:**
```json
[
  {
    "id": "proj-555",
    "title": "API Gateway Service",
    "similarity_score": 0.84,
    "type": "project",
    "metadata": {
      "status": "active",
      "tags": ["API", "gateway", "routing"],
      "plan_count": 8,
      "conversation_count": 3
    }
  }
]
```

**Example cURL:**
```bash
curl http://localhost:8000/search/similar-projects/proj-123?limit=5
```

**Status Codes:**
- `200 OK`: Successfully retrieved similar projects
- `404 Not Found`: Source project not found
- `500 Internal Server Error`: Search failed

**Use Cases:**
- "Show me related projects"
- "What other projects use similar technologies?"
- "Find projects with similar scope"

---

## Error Responses

All endpoints return consistent error responses:

**Example Error:**
```json
{
  "detail": "Search failed: Vector store not initialized"
}
```

**Common Error Scenarios:**
- **Vector store not found**: Run the re-indexing script first
- **Invalid query**: Check request payload format
- **Plan/Project not found**: Verify ID exists in database
- **Embedding service unavailable**: Check Requesty API configuration

---

## Best Practices

### Query Optimization

**Good Queries:**
- "implement user authentication with JWT tokens"
- "database migration strategy for PostgreSQL"
- "real-time notification system architecture"

**Poor Queries:**
- "plan" (too vague)
- "fix bug" (not specific enough)
- Single keywords (use phrases instead)

### Filtering

**Effective Filtering:**
```json
{
  "query": "authentication",
  "project_id": "proj-123",
  "status": ["in_progress", "completed"],
  "limit": 10
}
```

### Pagination

For large result sets, use the `limit` parameter and implement client-side pagination:
```json
{
  "query": "microservices",
  "limit": 10
}
```

**Note:** The API does not currently support offset-based pagination. To get more results, increase the `limit` parameter (max: 50).

---

## Performance Considerations

### Response Times
- **Typical**: 100-300ms
- **With large corpus**: 300-500ms
- **Cold start**: May take 1-2s on first query

### Optimization Tips
1. **Keep queries concise**: 5-20 words is optimal
2. **Use specific project filters**: Reduces search space
3. **Limit results appropriately**: Don't request more than needed
4. **Cache frequently-used results**: Client-side caching recommended

### Rate Limiting
Currently no rate limiting is enforced for search endpoints in development. Production deployments should implement rate limiting at the API gateway level.

---

## Integration Examples

### Python
```python
import requests

# Search plans
response = requests.post(
    "http://localhost:8000/search/plans",
    json={
        "query": "authentication implementation",
        "project_id": "proj-123",
        "limit": 5
    }
)
results = response.json()["results"]

for result in results:
    print(f"{result['title']} - Score: {result['score']:.2f}")
```

### JavaScript/TypeScript
```javascript
// Search projects
const response = await fetch('http://localhost:8000/search/projects', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'microservices architecture',
    limit: 5
  })
});

const data = await response.json();
console.log(`Found ${data.total_found} projects`);
```

### cURL
```bash
# Get related plans
curl -X GET "http://localhost:8000/search/related-plans/plan-123?limit=5" \
  -H "Accept: application/json"
```

---

## Vector Store Architecture

### Storage Structure
```
vector_store/
├── devplans/          # Plan embeddings
│   ├── index.faiss
│   └── index.pkl
├── projects/          # Project embeddings
│   ├── index.faiss
│   └── index.pkl
└── documents/         # Original document embeddings
    ├── index.faiss
    └── index.pkl
```

### Embedding Model
- **Model**: Requesty `embedding-001`
- **Dimensions**: 1536
- **Technology**: FAISS (Facebook AI Similarity Search)

### Indexing Process
1. **Plan created** → Parsed into sections → Embedded → Stored in FAISS
2. **Plan updated** → Old entries removed → New entries added
3. **Plan deleted** → All associated entries removed

---

## Troubleshooting

### "Vector store not found"
**Solution:** Run the bulk re-indexing script:
```bash
python -m backend.scripts.reindex_all
```

### "No results found"
**Possible causes:**
1. No plans/projects indexed yet
2. Query too specific or contains typos
3. Index needs to be rebuilt

**Solution:** Check if data exists and try a broader query.

### "Search taking too long"
**Possible causes:**
1. Large corpus (10,000+ documents)
2. Complex query
3. Cold start (first query after restart)

**Solution:** Use project filters, reduce result limit, or warm up the index.

---

## Future Enhancements

### Planned Features
- [ ] Faceted search with tag filters
- [ ] Date range filtering
- [ ] Advanced query syntax (AND, OR, NOT)
- [ ] Highlighting matched text in results
- [ ] Offset-based pagination
- [ ] Real-time search suggestions
- [ ] Search analytics and query logs

### API Version 2.0 (Planned)
- GraphQL support
- WebSocket streaming results
- Multi-language support
- Advanced relevance tuning

---

## Support

For issues, questions, or feature requests related to the Search API:
- Check `PHASE4_PROGRESS.md` for implementation status
- Review `nextphase.md` for roadmap details
- See main `README.md` for general system documentation

**Last Updated:** 2025-10-01  
**API Version:** 1.0  
**Status:** Production-ready backend, frontend integration complete
