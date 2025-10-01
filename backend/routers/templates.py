"""Prompt templates API routes."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter

from ..prompt_templates import get_all_templates, get_categories, get_template

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=Dict[str, Dict[str, str]])
async def list_templates():
    """Get all available prompt templates."""
    return get_all_templates()


@router.get("/categories", response_model=List[str])
async def list_categories():
    """Get all template categories."""
    return get_categories()


@router.get("/{template_id}", response_model=Dict[str, str])
async def get_template_by_id(template_id: str):
    """Get a specific template by ID."""
    template = get_template(template_id)
    if not template:
        return {"error": f"Template '{template_id}' not found"}
    return template
