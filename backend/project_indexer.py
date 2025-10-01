"""Index project metadata and conversation summaries for project memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from loguru import logger
from langchain_community.vectorstores import FAISS

try:
    from .config import settings
    from .indexing.requesty_embeddings import RequestyEmbeddings
    from .requesty_client import RequestyClient
except ImportError:  # pragma: no cover - allow execution as standalone script
    from config import settings
    from indexing.requesty_embeddings import RequestyEmbeddings
    from requesty_client import RequestyClient


class ProjectIndexer:
    """Manage vector indexing for projects and their conversation summaries."""

    def __init__(
        self,
        *,
        vector_path: Optional[str] = None,
        requesty_client: Optional[RequestyClient] = None,
    ) -> None:
        self.vector_path = Path(vector_path or settings.PROJECT_VECTOR_STORE_PATH)
        self.vector_path.mkdir(parents=True, exist_ok=True)

        self.client = requesty_client or RequestyClient()
        self.embeddings = RequestyEmbeddings(self.client)
        self.vector_store: Optional[FAISS] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def index_project(self, project: Mapping[str, Any]) -> Dict[str, Any]:
        payload = self._normalise_project(project)
        text = self._project_text(payload)
        doc_id = f"project::{payload['project_id']}"

        store = self._load_vector_store()
        if store is None:
            store = FAISS.from_texts([text], self.embeddings, metadatas=[payload], ids=[doc_id])
        else:
            existing = self._collect_ids(store, target_id=doc_id)
            if existing:
                store.delete(existing)
            store.add_texts([text], metadatas=[payload], ids=[doc_id])

        store.save_local(str(self.vector_path))
        self.vector_store = store
        logger.info("Indexed project %s", payload["project_id"])
        return {"indexed": 1}

    def index_conversation(self, conversation: Mapping[str, Any]) -> Dict[str, Any]:
        payload = self._normalise_conversation(conversation)
        text = self._conversation_text(payload)
        doc_id = f"conversation::{payload['conversation_id']}"

        store = self._load_vector_store()
        if store is None:
            store = FAISS.from_texts([text], self.embeddings, metadatas=[payload], ids=[doc_id])
        else:
            existing = self._collect_ids(store, target_id=doc_id)
            if existing:
                store.delete(existing)
            store.add_texts([text], metadatas=[payload], ids=[doc_id])

        store.save_local(str(self.vector_path))
        self.vector_store = store
        logger.info("Indexed conversation %s for project %s", payload["conversation_id"], payload["project_id"])
        return {"indexed": 1}

    def remove_project(self, project_id: str) -> bool:
        store = self._load_vector_store()
        if not store:
            return False
        doc_ids = self._collect_ids(store, prefix=f"project::{project_id}")
        if not doc_ids:
            return False
        store.delete(doc_ids)
        store.save_local(str(self.vector_path))
        logger.info("Removed project %s from project index", project_id)
        return True

    def remove_conversation(self, conversation_id: str) -> bool:
        store = self._load_vector_store()
        if not store:
            return False
        doc_ids = self._collect_ids(store, prefix=f"conversation::{conversation_id}")
        if not doc_ids:
            return False
        store.delete(doc_ids)
        store.save_local(str(self.vector_path))
        logger.info("Removed conversation %s from project index", conversation_id)
        return True

    def reload(self) -> None:
        self.vector_store = None
        self._load_vector_store()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_vector_store(self) -> Optional[FAISS]:
        if self.vector_store is not None:
            return self.vector_store

        index_file = self.vector_path / "index.faiss"
        if not index_file.exists():
            return None

        try:
            self.vector_store = FAISS.load_local(
                str(self.vector_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load project vector store: %s", exc)
            self.vector_store = None
        return self.vector_store

    def _collect_ids(self, store: FAISS, target_id: Optional[str] = None, prefix: Optional[str] = None) -> list[str]:
        docstore = getattr(store, "docstore", None)
        if not docstore:
            return []
        data = getattr(docstore, "_dict", {})
        results = []
        for doc_id in data.keys():
            if target_id and doc_id == target_id:
                results.append(doc_id)
            elif prefix and doc_id.startswith(prefix):
                results.append(doc_id)
        return results

    def _normalise_project(self, project: Mapping[str, Any]) -> Dict[str, Any]:
        tags = project.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        return {
            "type": "project",
            "project_id": project.get("id") or project.get("project_id"),
            "name": project.get("name"),
            "description": project.get("description"),
            "status": project.get("status"),
            "tags": tags,
            "plan_count": project.get("plan_count", 0),
            "conversation_count": project.get("conversation_count", 0),
            "updated_at": project.get("updated_at"),
            "repository_path": project.get("repository_path"),
        }

    def _project_text(self, project: Mapping[str, Any]) -> str:
        tag_text = ", ".join(project.get("tags", [])) or "no tags"
        description = project.get("description") or "No description provided."
        return (
            f"Project: {project.get('name')}\n"
            f"Status: {project.get('status')}\n"
            f"Tags: {tag_text}\n"
            f"Plans: {project.get('plan_count')} | Conversations: {project.get('conversation_count')}\n"
            f"Repository: {project.get('repository_path') or 'n/a'}\n"
            f"Summary: {description}"
        )

    def _normalise_conversation(self, conversation: Mapping[str, Any]) -> Dict[str, Any]:
        generated_plans = conversation.get("generated_plans") or []
        return {
            "type": "conversation",
            "conversation_id": conversation.get("id") or conversation.get("session_id"),
            "project_id": conversation.get("project_id"),
            "started_at": conversation.get("started_at"),
            "ended_at": conversation.get("ended_at"),
            "summary": conversation.get("summary") or "",
            "generated_plans": generated_plans,
            "message_count": conversation.get("message_count"),
        }

    def _conversation_text(self, conversation: Mapping[str, Any]) -> str:
        summary = conversation.get("summary") or "No summary available."
        plans = ", ".join(conversation.get("generated_plans", [])) or "None"
        return (
            f"Conversation Summary: {summary}\n"
            f"Generated Plans: {plans}\n"
            f"Started: {conversation.get('started_at')} | Ended: {conversation.get('ended_at')}\n"
            f"Message Count: {conversation.get('message_count') or 'unknown'}"
        )
