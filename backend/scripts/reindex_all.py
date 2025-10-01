"""
Bulk re-indexing script for all development plans and projects.

This script reprocesses all existing plans and projects in the database,
updating their vector store entries with the latest embeddings.

Usage:
    # Dry run (show what would be indexed)
    python -m backend.scripts.reindex_all --dry-run

    # Index plans only
    python -m backend.scripts.reindex_all --plans-only

    # Index projects only
    python -m backend.scripts.reindex_all --projects-only

    # Full re-index with custom batch size
    python -m backend.scripts.reindex_all --batch-size 20

    # Force re-index even if already indexed
    python -m backend.scripts.reindex_all --force
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from tqdm import tqdm

try:
    from backend.auto_indexer import AutoIndexer
    from backend.config import settings
    from backend.database import get_async_session_context
    from backend.devplan_processor import DevPlanProcessor
    from backend.project_indexer import ProjectIndexer
    from backend.storage.conversation_store import ConversationStore
    from backend.storage.plan_store import DevPlanStore
    from backend.storage.project_store import ProjectStore
except ImportError:
    logger.error("Failed to import backend modules. Ensure you're running from project root.")
    sys.exit(1)


class ReindexStats:
    """Track indexing statistics."""

    def __init__(self):
        self.plans_processed = 0
        self.plans_indexed = 0
        self.plans_failed = 0
        self.projects_processed = 0
        self.projects_indexed = 0
        self.projects_failed = 0
        self.conversations_processed = 0
        self.conversations_indexed = 0
        self.conversations_failed = 0

    def summary(self) -> str:
        return (
            f"\n{'='*60}\n"
            f"Re-indexing Complete\n"
            f"{'='*60}\n"
            f"Plans:         {self.plans_indexed}/{self.plans_processed} indexed "
            f"({self.plans_failed} failed)\n"
            f"Projects:      {self.projects_indexed}/{self.projects_processed} indexed "
            f"({self.projects_failed} failed)\n"
            f"Conversations: {self.conversations_indexed}/{self.conversations_processed} indexed "
            f"({self.conversations_failed} failed)\n"
            f"{'='*60}\n"
        )


async def reindex_plans(
    *,
    batch_size: int = 10,
    dry_run: bool = False,
    force: bool = False,
) -> ReindexStats:
    """Re-index all development plans."""
    stats = ReindexStats()
    processor = DevPlanProcessor()

    async with get_async_session_context() as session:
        plan_store = DevPlanStore(session)

        logger.info("Fetching all plans from database...")
        plans = await plan_store.list_plans(limit=10000)  # Large limit to get all
        stats.plans_processed = len(plans)

        if not plans:
            logger.warning("No plans found in database")
            return stats

        logger.info(f"Found {len(plans)} plans to {'simulate' if dry_run else 'index'}")

        with tqdm(total=len(plans), desc="Indexing Plans", unit="plan") as pbar:
            batch = []
            for plan in plans:
                # Get the latest version content
                latest_version = next(
                    (v for v in plan.versions if v.version_number == plan.current_version),
                    None
                )

                if not latest_version or not latest_version.content:
                    logger.debug(f"Skipping plan {plan.id}: no content")
                    stats.plans_failed += 1
                    pbar.update(1)
                    continue

                batch.append((plan, latest_version.content))

                if len(batch) >= batch_size:
                    await _process_plan_batch(batch, processor, stats, dry_run)
                    batch = []
                    pbar.update(batch_size)

            # Process remaining plans
            if batch:
                await _process_plan_batch(batch, processor, stats, dry_run)
                pbar.update(len(batch))

    return stats


async def _process_plan_batch(
    batch: list,
    processor: DevPlanProcessor,
    stats: ReindexStats,
    dry_run: bool,
) -> None:
    """Process a batch of plans in parallel."""
    for plan, content in batch:
        if dry_run:
            logger.info(f"[DRY RUN] Would index plan: {plan.title} (ID: {plan.id})")
            stats.plans_indexed += 1
            continue

        try:
            # Convert plan ORM object to dict for processor
            plan_dict = {
                "id": plan.id,
                "project_id": plan.project_id,
                "title": plan.title,
                "status": plan.status,
                "current_version": plan.current_version,
                "conversation_id": plan.conversation_id,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
                "metadata": plan.metadata_dict or {},
            }

            result = processor.process_plan(plan_dict, content=content)

            if result.get("indexed", 0) > 0:
                stats.plans_indexed += 1
                logger.debug(f"Indexed plan {plan.id}: {result['indexed']} chunks")
            else:
                stats.plans_failed += 1
                logger.warning(f"Failed to index plan {plan.id}")

        except Exception as exc:
            stats.plans_failed += 1
            logger.error(f"Error indexing plan {plan.id}: {exc}")


async def reindex_projects(
    *,
    batch_size: int = 10,
    dry_run: bool = False,
    force: bool = False,
) -> ReindexStats:
    """Re-index all projects."""
    stats = ReindexStats()
    indexer = ProjectIndexer()

    async with get_async_session_context() as session:
        project_store = ProjectStore(session)

        logger.info("Fetching all projects from database...")
        projects = await project_store.list_projects(limit=10000)
        stats.projects_processed = len(projects)

        if not projects:
            logger.warning("No projects found in database")
            return stats

        logger.info(f"Found {len(projects)} projects to {'simulate' if dry_run else 'index'}")

        with tqdm(total=len(projects), desc="Indexing Projects", unit="project") as pbar:
            for project in projects:
                if dry_run:
                    logger.info(f"[DRY RUN] Would index project: {project.name} (ID: {project.id})")
                    stats.projects_indexed += 1
                    pbar.update(1)
                    continue

                try:
                    project_dict = {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "tags": project.tags or [],
                        "plan_count": project.plan_count,
                        "conversation_count": project.conversation_count,
                        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                        "repository_path": project.repository_path,
                    }

                    result = indexer.index_project(project_dict)

                    if result.get("indexed", 0) > 0:
                        stats.projects_indexed += 1
                        logger.debug(f"Indexed project {project.id}")
                    else:
                        stats.projects_failed += 1
                        logger.warning(f"Failed to index project {project.id}")

                except Exception as exc:
                    stats.projects_failed += 1
                    logger.error(f"Error indexing project {project.id}: {exc}")

                pbar.update(1)

    return stats


async def reindex_conversations(
    *,
    batch_size: int = 10,
    dry_run: bool = False,
    force: bool = False,
) -> ReindexStats:
    """Re-index all conversations."""
    stats = ReindexStats()
    indexer = ProjectIndexer()

    async with get_async_session_context() as session:
        conversation_store = ConversationStore(session)

        logger.info("Fetching all conversations from database...")
        conversations = await conversation_store.list_sessions(limit=10000)
        stats.conversations_processed = len(conversations)

        if not conversations:
            logger.warning("No conversations found in database")
            return stats

        logger.info(f"Found {len(conversations)} conversations to {'simulate' if dry_run else 'index'}")

        with tqdm(total=len(conversations), desc="Indexing Conversations", unit="conv") as pbar:
            for convo in conversations:
                # Only index conversations with summaries
                if not convo.summary:
                    logger.debug(f"Skipping conversation {convo.id}: no summary")
                    pbar.update(1)
                    continue

                if dry_run:
                    logger.info(f"[DRY RUN] Would index conversation: {convo.id}")
                    stats.conversations_indexed += 1
                    pbar.update(1)
                    continue

                try:
                    convo_dict = {
                        "id": convo.id,
                        "project_id": convo.project_id,
                        "summary": convo.summary,
                        "generated_plans": convo.generated_plans or [],
                        "started_at": convo.started_at.isoformat() if convo.started_at else None,
                        "ended_at": convo.ended_at.isoformat() if convo.ended_at else None,
                        "message_count": len(convo.messages) if convo.messages else 0,
                    }

                    result = indexer.index_conversation(convo_dict)

                    if result.get("indexed", 0) > 0:
                        stats.conversations_indexed += 1
                        logger.debug(f"Indexed conversation {convo.id}")
                    else:
                        stats.conversations_failed += 1
                        logger.warning(f"Failed to index conversation {convo.id}")

                except Exception as exc:
                    stats.conversations_failed += 1
                    logger.error(f"Error indexing conversation {convo.id}: {exc}")

                pbar.update(1)

    return stats


async def main():
    """Main entry point for re-indexing script."""
    parser = argparse.ArgumentParser(
        description="Re-index all development plans and projects into vector stores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be indexed without actually indexing",
    )
    parser.add_argument(
        "--plans-only",
        action="store_true",
        help="Only re-index development plans",
    )
    parser.add_argument(
        "--projects-only",
        action="store_true",
        help="Only re-index projects",
    )
    parser.add_argument(
        "--conversations-only",
        action="store_true",
        help="Only re-index conversations",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of items to process in each batch (default: 10)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-index even if items are already indexed",
    )

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Development Planning Re-indexing Script")
    logger.info("="*60)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE INDEXING'}")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info(f"Force: {args.force}")
    logger.info("="*60)

    total_stats = ReindexStats()

    # Determine what to index
    index_plans = not (args.projects_only or args.conversations_only)
    index_projects = not (args.plans_only or args.conversations_only)
    index_conversations = not (args.plans_only or args.projects_only)

    try:
        if index_plans:
            logger.info("\n📄 Re-indexing development plans...")
            plan_stats = await reindex_plans(
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                force=args.force,
            )
            total_stats.plans_processed = plan_stats.plans_processed
            total_stats.plans_indexed = plan_stats.plans_indexed
            total_stats.plans_failed = plan_stats.plans_failed

        if index_projects:
            logger.info("\n📁 Re-indexing projects...")
            project_stats = await reindex_projects(
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                force=args.force,
            )
            total_stats.projects_processed = project_stats.projects_processed
            total_stats.projects_indexed = project_stats.projects_indexed
            total_stats.projects_failed = project_stats.projects_failed

        if index_conversations:
            logger.info("\n💬 Re-indexing conversations...")
            conv_stats = await reindex_conversations(
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                force=args.force,
            )
            total_stats.conversations_processed = conv_stats.conversations_processed
            total_stats.conversations_indexed = conv_stats.conversations_indexed
            total_stats.conversations_failed = conv_stats.conversations_failed

        logger.info(total_stats.summary())

        if args.dry_run:
            logger.info("DRY RUN completed. No changes were made.")
        else:
            logger.info("✅ Re-indexing completed successfully!")

    except Exception as exc:
        logger.error(f"Re-indexing failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
