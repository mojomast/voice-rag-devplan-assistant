"""Utility helpers for lightweight small-talk responses.

These responses improve UX by handling greetings or quick personal
questions without invoking the full RAG pipeline.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

_SMALL_TALK_PATTERNS: Iterable[tuple[set[str], str]] = [
    (
        {
            "hi",
            "hello",
            "hey",
            "hiya",
            "hey there",
            "hello there",
            "hi there",
            "good morning",
            "good afternoon",
            "good evening",
            "whats up",
            "what's up",
            "what is up",
            "wassup",
        },
    "Hi! I'm the DevPlan Assistant. I'm here to help you explore your project documents and plans. What's up on your side?",
    ),
    (
        {
            "what is your name",
            "whats your name",
            "what's your name",
            "who are you",
            "who r you",
            "who r u",
            "who are u",
        },
        "I'm the DevPlan Assistant, your voice-enabled planning companion for this workspace.",
    ),
    (
        {"thank you", "thanks", "thx", "ty"},
        "You're welcome! Let me know if you'd like to dig into any documents or plans.",
    ),
    (
        {"bye", "goodbye", "see you", "see ya", "later", "talk to you later"},
        "Bye for now! I'm ready whenever you want to keep planning.",
    ),
    (
        {
            "can you create a new file",
            "can you make a new file",
            "create a new file",
            "make a new file",
        },
        "I can't create files directly from this chat, but you can upload new documents in the sidebar and I'll index them for planning.",
    ),
]


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", "", text.lower())
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def get_small_talk_response(query: str) -> Optional[str]:
    """Return a canned response for lightweight conversational prompts."""
    if not query:
        return None

    normalized = _normalize(query)
    if not normalized:
        return None

    for triggers, response in _SMALL_TALK_PATTERNS:
        for phrase in triggers:
            if normalized == phrase or normalized.startswith(f"{phrase} "):
                return response
    return None
