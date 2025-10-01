"""Seed sample projects and development plans for Phase 4 testing.

Run with:
    python -m backend.scripts.seed_sample_data

The script is idempotent and will exit without changes if projects already exist.
"""
from __future__ import annotations

import asyncio
from textwrap import dedent

from loguru import logger

from ..database import get_async_session_context
from ..storage.plan_store import DevPlanStore
from ..storage.project_store import ProjectStore


SAMPLE_PROJECTS = [
    {
        "name": "RAG Assistant Pilot",
        "description": "Pilot project to integrate retrieval-augmented planning workflows.",
        "status": "active",
        "tags": ["rag", "planning", "pilot"],
        "repository_path": "github.com/example/rag-assistant",
    },
    {
        "name": "Payments Modernisation",
        "description": "Modernise payments stack with service mesh, observability, and compliance safeguards.",
        "status": "active",
        "tags": ["payments", "modernisation", "compliance"],
        "repository_path": "github.com/example/payments-modernisation",
    },
]

SAMPLE_PLANS = [
    {
        "title": "Authentication Hardening Rollout",
        "content": dedent(
            """
            # Authentication Hardening Rollout

            ## Objectives
            - Strengthen MFA coverage
            - Introduce adaptive risk scoring

            ## Milestones
            1. Audit existing auth flows
            2. Deploy updated MFA enrollment
            3. Launch monitoring dashboards

            ## Deliverables
            - Updated auth documentation
            - Metrics dashboard in Grafana
            """
        ).strip(),
        "status": "approved",
        "metadata": {"category": "security"},
        "change_summary": "Initial hardening plan",
    },
    {
        "title": "Service Mesh Migration",
        "content": dedent(
            """
            # Service Mesh Migration

            ## Objectives
            - Adopt mesh-based traffic management
            - Enable zero-trust communication between services

            ## Phases
            1. Bootstrap Istio staging environment
            2. Migrate core services and configure policies
            3. Roll out observability dashboards and alerts

            ## Success Metrics
            - <200ms P95 intra-service latency
            - 100% mutual TLS coverage
            - Automated policy drift detection
            """
        ).strip(),
        "status": "in_progress",
        "metadata": {"category": "platform"},
        "change_summary": "v1 migration outline",
    },
]


async def seed() -> None:
    async with get_async_session_context() as session:
        project_store = ProjectStore(session)
        plan_store = DevPlanStore(session)

        existing_projects = await project_store.list_projects(limit=1)
        if existing_projects:
            logger.info("Projects already exist in database; skipping seed.")
            return

        for project_data, plan_data in zip(SAMPLE_PROJECTS, SAMPLE_PLANS):
            project = await project_store.create_project(**project_data)
            plan = await plan_store.create_plan(project_id=project.id, conversation_id=None, **plan_data)
            logger.success(
                "Seeded project {project} with plan {plan}",
                project=project.name,
                plan=plan.title,
            )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
