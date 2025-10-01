"""LangChain embeddings adapter that proxies to the Requesty client."""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from langchain.embeddings.base import Embeddings

try:
    from ..config import settings
    from ..requesty_client import RequestyClient
except ImportError:  # pragma: no cover - allow execution as script
    from config import settings
    from requesty_client import RequestyClient


class RequestyEmbeddings(Embeddings):
    """Embedding helper that wraps ``RequestyClient`` for LangChain compatibility."""

    def __init__(self, client: Optional[RequestyClient] = None, model: Optional[str] = None) -> None:
        self.client = client or RequestyClient()
        self.model = model or settings.REQUESTY_EMBEDDING_MODEL

    # ``Embeddings`` base class uses ``embed_documents``/``embed_query``
    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        payload = list(texts)
        if not payload:
            return []
        return self.client.embed_texts(payload, model=self.model)

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []

    # Convenience alias for compatibility with some consumers
    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        return self.embed_documents(texts)
