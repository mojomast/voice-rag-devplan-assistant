"""Semantic search API endpoints for plans and projects."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..rag_handler import RAGHandler
from ..storage.plan_store import DevPlanStore
from ..storage.project_store import ProjectStore

router = APIRouter(prefix="/search", tags=["search"])


# -------------------------------------------------------------------------
# Request/Response Models
# -------------------------------------------------------------------------
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    status: Optional[List[str]] = Field(None, description="Filter by status values")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class SearchResult(BaseModel):
    id: str
    title: str
    type: str  # 'devplan' or 'project'
    content_preview: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_found: int


class RelatedItem(BaseModel):
    id: str
    title: str
    similarity_score: float
    type: str
    metadata: dict


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------
def _get_rag_handler() -> RAGHandler:
    """Dependency to get RAG handler instance."""
    from ..rag_handler import RAGHandler
    return RAGHandler()


# -------------------------------------------------------------------------
# Search Endpoints
# -------------------------------------------------------------------------
@router.post("/plans", response_model=SearchResponse)
async def search_plans(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Semantic search across development plans.
    
    Returns plans ranked by semantic similarity to the query.
    """
    logger.info(
        f"Plan search request: query='{request.query[:50]}...', "
        f"project_id={request.project_id}, limit={request.limit}"
    )
    
    try:
        rag_handler = _get_rag_handler()
        
        # Build metadata filter
        metadata_filter = {"type": "devplan"}
        if request.project_id:
            metadata_filter["project_id"] = request.project_id
        if request.status:
            # Note: Vector stores may not support multi-value filters efficiently
            # This will filter in post-processing if needed
            pass
        
        # Perform vector search
        raw_results = rag_handler.search(
            query=request.query,
            k=request.limit * 2,  # Fetch more to allow for filtering
            metadata_filter=metadata_filter,
        )
        
        # Post-process results
        search_results: List[SearchResult] = []
        plan_store = DevPlanStore(session)
        
        for item in raw_results:
            if len(search_results) >= request.limit:
                break
                
            metadata = item.get("metadata", {})
            plan_id = metadata.get("plan_id")
            
            # Apply status filter if provided
            if request.status and metadata.get("status") not in request.status:
                continue
            
            # Get plan details for enrichment
            plan = await plan_store.get_plan(plan_id) if plan_id else None
            
            search_results.append(
                SearchResult(
                    id=plan_id or metadata.get("id", "unknown"),
                    title=metadata.get("plan_title", "Untitled Plan"),
                    type="devplan",
                    content_preview=item.get("content", "")[:300],
                    score=float(item.get("score", 0.0)),
                    metadata={
                        "project_id": metadata.get("project_id"),
                        "status": metadata.get("status"),
                        "section_title": metadata.get("section_title"),
                        "version": metadata.get("version"),
                        "updated_at": plan.updated_at.isoformat() if plan and plan.updated_at else None,
                    }
                )
            )
        
        logger.info(f"Plan search completed: {len(search_results)} results found")
        
        return SearchResponse(
            results=search_results,
            query=request.query,
            total_found=len(search_results),
        )
        
    except Exception as exc:
        logger.error(f"Plan search failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}"
        )


@router.post("/projects", response_model=SearchResponse)
async def search_projects(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Semantic search across projects and their metadata.
    
    Returns projects ranked by semantic similarity to the query.
    """
    logger.info(
        f"Project search request: query='{request.query[:50]}...', "
        f"limit={request.limit}"
    )
    
    try:
        rag_handler = _get_rag_handler()
        
        # Build metadata filter
        metadata_filter = {"type": "project"}
        
        # Perform vector search
        raw_results = rag_handler.search(
            query=request.query,
            k=request.limit,
            metadata_filter=metadata_filter,
        )
        
        # Process results
        search_results: List[SearchResult] = []
        project_store = ProjectStore(session)
        
        for item in raw_results:
            metadata = item.get("metadata", {})
            project_id = metadata.get("project_id")
            
            # Get project details
            project = await project_store.get_project(project_id) if project_id else None
            
            search_results.append(
                SearchResult(
                    id=project_id or metadata.get("id", "unknown"),
                    title=metadata.get("name", "Untitled Project"),
                    type="project",
                    content_preview=item.get("content", "")[:300],
                    score=float(item.get("score", 0.0)),
                    metadata={
                        "status": metadata.get("status"),
                        "tags": metadata.get("tags", []),
                        "plan_count": metadata.get("plan_count", 0),
                        "conversation_count": metadata.get("conversation_count", 0),
                        "updated_at": project.updated_at.isoformat() if project and project.updated_at else None,
                    }
                )
            )
        
        logger.info(f"Project search completed: {len(search_results)} results found")
        
        return SearchResponse(
            results=search_results,
            query=request.query,
            total_found=len(search_results),
        )
        
    except Exception as exc:
        logger.error(f"Project search failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}"
        )


@router.get("/related-plans/{plan_id}", response_model=List[RelatedItem])
async def get_related_plans(
    plan_id: str,
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    """
    Find plans semantically related to the specified plan.
    
    Uses the plan's content to find similar plans across all projects.
    """
    logger.info(f"Related plans request: plan_id={plan_id}, limit={limit}")
    
    try:
        plan_store = DevPlanStore(session)
        plan = await plan_store.get_plan(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {plan_id} not found"
            )
        
        # Get the latest version content
        latest_version = next(
            (v for v in plan.versions if v.version_number == plan.current_version),
            None
        )
        
        if not latest_version or not latest_version.content:
            return []
        
        # Use plan title and a snippet of content as search query
        query = f"{plan.title}. {latest_version.content[:500]}"
        
        rag_handler = _get_rag_handler()
        raw_results = rag_handler.search(
            query=query,
            k=limit + 5,  # Get extra to filter out self
            metadata_filter={"type": "devplan"},
        )
        
        related_items: List[RelatedItem] = []
        for item in raw_results:
            metadata = item.get("metadata", {})
            related_plan_id = metadata.get("plan_id")
            
            # Skip self-reference
            if related_plan_id == plan_id:
                continue
            
            if len(related_items) >= limit:
                break
            
            related_items.append(
                RelatedItem(
                    id=related_plan_id or "unknown",
                    title=metadata.get("plan_title", "Untitled"),
                    similarity_score=float(item.get("score", 0.0)),
                    type="devplan",
                    metadata={
                        "project_id": metadata.get("project_id"),
                        "status": metadata.get("status"),
                        "version": metadata.get("version"),
                    }
                )
            )
        
        logger.info(f"Found {len(related_items)} related plans for {plan_id}")
        return related_items
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Related plans search failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find related plans: {str(exc)}"
        )


@router.get("/similar-projects/{project_id}", response_model=List[RelatedItem])
async def get_similar_projects(
    project_id: str,
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    """
    Find projects semantically similar to the specified project.
    
    Uses project metadata (name, description, tags) to find similar projects.
    """
    logger.info(f"Similar projects request: project_id={project_id}, limit={limit}")
    
    try:
        project_store = ProjectStore(session)
        project = await project_store.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Build search query from project metadata
        tags_text = ", ".join(project.tags) if project.tags else ""
        query = f"{project.name}. {project.description or ''} Tags: {tags_text}"
        
        rag_handler = _get_rag_handler()
        raw_results = rag_handler.search(
            query=query,
            k=limit + 5,  # Get extra to filter out self
            metadata_filter={"type": "project"},
        )
        
        similar_items: List[RelatedItem] = []
        for item in raw_results:
            metadata = item.get("metadata", {})
            similar_project_id = metadata.get("project_id")
            
            # Skip self-reference
            if similar_project_id == project_id:
                continue
            
            if len(similar_items) >= limit:
                break
            
            similar_items.append(
                RelatedItem(
                    id=similar_project_id or "unknown",
                    title=metadata.get("name", "Untitled"),
                    similarity_score=float(item.get("score", 0.0)),
                    type="project",
                    metadata={
                        "status": metadata.get("status"),
                        "tags": metadata.get("tags", []),
                        "plan_count": metadata.get("plan_count", 0),
                        "conversation_count": metadata.get("conversation_count", 0),
                    }
                )
            )
        
        logger.info(f"Found {len(similar_items)} similar projects for {project_id}")
        return similar_items
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Similar projects search failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar projects: {str(exc)}"
        )
