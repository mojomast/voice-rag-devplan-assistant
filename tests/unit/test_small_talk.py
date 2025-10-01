import types

import pytest

from backend.small_talk import get_small_talk_response
from backend.rag_handler import RAGHandler


@pytest.mark.parametrize("prompt", ["Hi there!", "whats up?", "What's up"])
def test_small_talk_greeting_response(prompt):
    response = get_small_talk_response(prompt)
    assert response is not None
    assert "Assistant" in response


def test_small_talk_no_match():
    assert get_small_talk_response("Tell me about sprint planning") is None


def test_rag_handler_small_talk_standard_mode_updates_memory():
    handler = object.__new__(RAGHandler)
    handler.test_mode = False
    handler.vector_store = None
    handler.memory = types.SimpleNamespace()

    recorded = []

    def add_user_message(message):
        recorded.append(("user", message))

    def add_ai_message(message):
        recorded.append(("ai", message))

    handler.memory.chat_memory = types.SimpleNamespace(
        add_user_message=add_user_message,
        add_ai_message=add_ai_message,
    )

    response = RAGHandler.ask_question(handler, "hello there")

    assert response["status"] == "success"
    assert response["metadata"]["response_type"] == "small_talk"
    assert recorded == [("user", "hello there"), ("ai", response["answer"])]


def test_small_talk_handles_capability_question():
    response = get_small_talk_response("Can you make a new file?")
    assert response is not None
    assert "upload" in response.lower()


def test_rag_handler_small_talk_test_mode_updates_history():
    handler = object.__new__(RAGHandler)
    handler.test_mode = True
    handler.vector_store = None
    handler._history_limit = 5
    handler._conversation_history = []

    response = RAGHandler.ask_question(handler, "who are you?")

    assert response["status"] == "success"
    assert response.get("test_mode") is True
    assert handler._conversation_history[-1]["type"] == "small_talk"
    assert handler._conversation_history[-1]["question"] == "who are you?"


def test_rag_handler_empty_query_returns_error():
    handler = object.__new__(RAGHandler)
    handler.test_mode = True
    handler.vector_store = None
    handler._history_limit = 5
    handler._conversation_history = []

    response = RAGHandler.ask_question(handler, "   ")

    assert response["status"] == "error"
    assert response.get("error") == "empty_query"
    assert handler._conversation_history[-1]["status"] == "error"
