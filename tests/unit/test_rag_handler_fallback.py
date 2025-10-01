from types import SimpleNamespace

import pytest

from backend.rag_handler import RAGHandler


class _FakeDoc:
    def __init__(self, content: str, source: str = "test_doc.txt", page: int = 1):
        self.page_content = content
        self.metadata = {"source": source, "page": page}


class _FakeChain:
    def __init__(self, answer: str, docs):
        self._answer = answer
        self._docs = docs

    def invoke(self, payload):
        return {"answer": self._answer, "source_documents": self._docs}


@pytest.fixture
def minimal_handler():
    handler = object.__new__(RAGHandler)
    handler.test_mode = False
    handler.vector_store = None
    handler.memory = None
    return handler


def test_context_summary_replaces_insufficient_answer(minimal_handler):
    handler = minimal_handler
    docs = [
        _FakeDoc(
            "engenius ap\n192.168.1.253 admin saladsalad\n2935506 marjolaine",
            source="engenius ap.txt",
        )
    ]
    handler.qa_chain = _FakeChain(
        "I don't have enough information in the provided documents to answer this question.",
        docs,
    )

    response = handler.ask_question("what do you think about the engenius file")

    assert response["status"] == "success"
    assert "engenius ap.txt" in response["answer"]
    assert response.get("metadata", {}).get("response_type") == "context_summary"
    assert response["sources"]


def test_insufficient_detector():
    assert RAGHandler._looks_like_insufficient_answer("I don't have enough information.")
    assert not RAGHandler._looks_like_insufficient_answer("The document lists credentials.")


def test_summary_builder_handles_empty_sources():
    assert RAGHandler._build_summary_from_sources([], "query") is None

    summary = RAGHandler._build_summary_from_sources(
        [{"source": "doc.txt", "content_preview": "Line one\nLine two"}],
        "query",
    )
    assert summary is not None
    assert "doc.txt" in summary
