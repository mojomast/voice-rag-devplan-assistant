from pathlib import Path

import pytest

from backend.devplan_processor import DevPlanProcessor
from backend.project_indexer import ProjectIndexer


class _FakeRequestyClient:
    def embed_texts(self, texts, model=None):  # noqa: D401 - simple deterministic embeddings
        embeddings = []
        for idx, _ in enumerate(texts, start=1):
            # Produce deterministic vectors with non-zero variance
            embeddings.append([float(idx)] * 16)
        return embeddings


@pytest.fixture()
def fake_client():
    return _FakeRequestyClient()


def _plan_payload(plan_id: str = "plan-123", project_id: str = "project-123"):
    return {
        "id": plan_id,
        "project_id": project_id,
        "title": "Voice Planning MVP",
        "status": "draft",
        "metadata": {"key_decisions": ["Focus on Requesty embeddings"]},
        "current_version": 1,
        "conversation_id": None,
        "created_at": "2025-09-30T12:00:00Z",
        "updated_at": "2025-09-30T12:00:00Z",
    }


def test_devplan_processor_creates_and_removes_index(tmp_path: Path, fake_client):
    processor = DevPlanProcessor(vector_path=str(tmp_path / "devplans"), requesty_client=fake_client)
    payload = _plan_payload()
    markdown = """# Voice Planning MVP\n\n## Overview\nBuild planning UI.\n\n## Rollout\nShip in phases."""

    result = processor.process_plan(payload, content=markdown)
    assert result["indexed"] >= 2
    assert processor.vector_store is not None
    assert (tmp_path / "devplans" / "index.faiss").exists()

    # Ensure embeddings are present
    store = processor.vector_store
    docs = store.similarity_search("planning", k=1)
    assert docs, "Expected at least one document in the devplan index"

    assert processor.remove_plan(payload["id"]) is True
    # Removing twice should be a no-op but return False
    assert processor.remove_plan(payload["id"]) is False


def test_project_indexer_indexes_project(tmp_path: Path, fake_client):
    indexer = ProjectIndexer(vector_path=str(tmp_path / "projects"), requesty_client=fake_client)
    project_payload = {
        "id": "project-xyz",
        "name": "Voice RAG Assistant",
        "description": "Voice-enabled development planner",
        "status": "active",
        "tags": ["voice", "planning"],
        "plan_count": 3,
        "conversation_count": 5,
        "updated_at": "2025-09-30T10:00:00Z",
        "repository_path": "/path/to/repo",
    }

    indexer.index_project(project_payload)
    assert indexer.vector_store is not None
    assert (tmp_path / "projects" / "index.faiss").exists()

    results = indexer.vector_store.similarity_search("development planner", k=1)
    assert results, "Expected similarity search to yield project metadata"

    indexer.remove_project(project_payload["id"])
    assert not indexer.vector_store.docstore._dict  # type: ignore[attr-defined]
