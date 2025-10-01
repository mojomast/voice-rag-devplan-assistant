"""Utilities for chunking and indexing development plans into the vector store."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from loguru import logger
from langchain_community.vectorstores import FAISS

try:
    from .config import settings
    from .indexing.requesty_embeddings import RequestyEmbeddings
    from .requesty_client import RequestyClient
except ImportError:  # pragma: no cover - allow execution as a standalone script
    from config import settings
    from indexing.requesty_embeddings import RequestyEmbeddings
    from requesty_client import RequestyClient


SECTION_PATTERN = re.compile(r"^(#{1,6})\\s+(.*)")
DEFAULT_PLAN_SECTION = "Overview"


@dataclass
class PlanSection:
    """Represents a logical slice of a development plan."""

    title: str
    content: str
    order: int


class DevPlanProcessor:
    """Process and index development plans using Requesty embeddings."""

    def __init__(
        self,
        *,
        vector_path: Optional[str] = None,
        requesty_client: Optional[RequestyClient] = None,
    ) -> None:
        self.vector_path = Path(vector_path or settings.DEVPLAN_VECTOR_STORE_PATH)
        self.vector_path.mkdir(parents=True, exist_ok=True)

        self.client = requesty_client or RequestyClient()
        self.embeddings = RequestyEmbeddings(self.client)
        self.vector_store: Optional[FAISS] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_plan(self, plan: Mapping[str, Any], *, content: str) -> Dict[str, Any]:
        """Index the latest version of a development plan."""

        if not content.strip():
            logger.warning("Skipping plan indexing; content is empty", plan_id=plan.get("id"))
            return {"indexed": 0, "skipped": True}

        sections = self._parse_markdown(content)
        entries = self._prepare_entries(plan, sections)

        if not entries.texts:
            logger.warning("No sections produced for plan %s", plan.get("id"))
            return {"indexed": 0, "skipped": True}

        store = self._load_vector_store()
        existing = self._collect_plan_ids(store, plan_id=plan.get("id")) if store else []

        if store is None:
            store = FAISS.from_texts(
                entries.texts,
                self.embeddings,
                metadatas=entries.metadatas,
                ids=entries.ids,
            )
        else:
            if existing:
                logger.debug("Removing %s existing index entries for plan %s", len(existing), plan.get("id"))
                store.delete(existing)
            store.add_texts(entries.texts, metadatas=entries.metadatas, ids=entries.ids)

        store.save_local(str(self.vector_path))
        self.vector_store = store

        logger.info(
            "Indexed development plan",
            plan_id=plan.get("id"),
            chunks=len(entries.ids),
            version=plan.get("current_version"),
        )
        return {"indexed": len(entries.ids), "skipped": False}

    def remove_plan(self, plan_id: str) -> bool:
        """Remove all indexed chunks for a plan."""

        store = self._load_vector_store()
        if not store:
            return False

        doc_ids = self._collect_plan_ids(store, plan_id)
        if not doc_ids:
            return False

        store.delete(doc_ids)
        store.save_local(str(self.vector_path))
        logger.info("Removed plan %s from vector index", plan_id)
        return True

    def reload(self) -> None:
        """Force reload of local vector store from disk."""
        self.vector_store = None
        self._load_vector_store()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @dataclass
    class _EntryBatch:
        texts: List[str]
        metadatas: List[Dict[str, Any]]
        ids: List[str]

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
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to load devplan vector store: %s", exc)
            self.vector_store = None
        return self.vector_store

    def _collect_plan_ids(self, store: FAISS, plan_id: Optional[str]) -> List[str]:
        if not plan_id:
            return []
        docstore = getattr(store, "docstore", None)
        if not docstore:
            return []
        data = getattr(docstore, "_dict", {})
        return [
            doc_id
            for doc_id, document in data.items()
            if isinstance(document.metadata, dict) and document.metadata.get("plan_id") == plan_id
        ]

    def _parse_markdown(self, content: str) -> List[PlanSection]:
        """Split plan markdown into logical sections."""

        sections: List[PlanSection] = []
        lines = content.splitlines()

        current_title = DEFAULT_PLAN_SECTION
        buffer: List[str] = []
        order = 0

        for line in lines:
            match = SECTION_PATTERN.match(line)
            if match and len(match.group(1)) <= 3:
                if buffer:
                    sections.extend(self._chunks_for_section(current_title, buffer, order))
                    order += 1
                    buffer = []
                heading = match.group(2).strip() or current_title
                current_title = heading
                buffer.append(line)
            else:
                buffer.append(line)

        if buffer:
            sections.extend(self._chunks_for_section(current_title, buffer, order))

        if not sections:
            sections.append(PlanSection(title=DEFAULT_PLAN_SECTION, content=content.strip(), order=0))

        return sections

    def _chunks_for_section(self, title: str, buffer: List[str], order: int) -> List[PlanSection]:
        text = "\n".join(buffer).strip()
        if not text:
            return []

        chunks = self._chunk_text(text, max_chars=1200)
        return [
            PlanSection(title=title, content=chunk, order=order * 100 + idx)
            for idx, chunk in enumerate(chunks)
        ]

    def _chunk_text(self, text: str, *, max_chars: int) -> List[str]:
        if len(text) <= max_chars:
            return [text]

        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for line in text.splitlines():
            line = line.rstrip()
            if current and current_len + len(line) > max_chars:
                chunks.append("\n".join(current).strip())
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len += len(line)

        if current:
            chunks.append("\n".join(current).strip())

        return chunks

    def _prepare_entries(self, plan: Mapping[str, Any], sections: Sequence[PlanSection]) -> _EntryBatch:
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        plan_id = plan.get("id")
        version = plan.get("current_version")
        base_metadata = self._plan_metadata(plan)

        for idx, section in enumerate(sections):
            chunk_id = f"plan::{plan_id}::v{version}::chunk::{section.order + idx}"
            metadata = {
                **base_metadata,
                "section_title": section.title,
                "section_order": section.order,
                "chunk_index": idx,
            }
            texts.append(section.content)
            metadatas.append(metadata)
            ids.append(chunk_id)

        # Add a whole-document chunk for plan-level retrieval
        full_id = f"plan::{plan_id}::v{version}::full"
        texts.append("\n\n".join(section.content for section in sections))
        metadatas.append({**base_metadata, "section_title": "__full__", "section_order": -1, "chunk_index": -1})
        ids.append(full_id)

        return self._EntryBatch(texts=texts, metadatas=metadatas, ids=ids)

    def _plan_metadata(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        metadata = {
            "type": "devplan",
            "plan_id": plan.get("id"),
            "plan_title": plan.get("title"),
            "project_id": plan.get("project_id"),
            "status": plan.get("status"),
            "version": plan.get("current_version"),
            "conversation_id": plan.get("conversation_id"),
            "created_at": plan.get("created_at"),
            "updated_at": plan.get("updated_at"),
        }
        extra = plan.get("metadata") or {}
        if isinstance(extra, Mapping):
            for key, value in extra.items():
                # Avoid collisions with reserved keys
                if key not in metadata:
                    metadata[f"meta_{key}"] = value
        return metadata
