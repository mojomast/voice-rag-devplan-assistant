from __future__ import annotations

import asyncio
import functools
import hashlib
import json
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from openai import OpenAI

try:
    from .config import settings
except ImportError:  # pragma: no cover - enables direct module imports in tests
    from config import settings


class RequestyClient:
    """Client wrapper that prioritises Requesty Router with graceful fallbacks."""

    def __init__(self) -> None:
        self.router_api_key = settings.ROUTER_API_KEY
        self.requesty_api_key = settings.REQUESTY_API_KEY  # Legacy fallback support
        self.openai_api_key = settings.OPENAI_API_KEY
        self.test_mode = settings.TEST_MODE

        self.default_chat_model = settings.REQUESTY_PLANNING_MODEL or settings.LLM_MODEL
        self.default_embedding_model = settings.REQUESTY_EMBEDDING_MODEL or settings.EMBEDDING_MODEL

        self.router_client: Optional[OpenAI] = None
        self.openai_client: Optional[OpenAI] = None
        self.use_router: bool = False

        if self.router_api_key:
            try:
                self.router_client = OpenAI(
                    api_key=self.router_api_key,
                    base_url="https://router.requesty.ai/v1",
                    default_headers={"Authorization": f"Bearer {self.router_api_key}"},
                )
                self.use_router = True
                logger.info("Requesty Router client initialised")
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(f"Failed to initialise Requesty Router client: {exc}")
                self.use_router = False

        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(f"Failed to initialise OpenAI fallback client: {exc}")
                self.openai_client = None

        if not self.use_router:
            if self.openai_client:
                logger.info("Using direct OpenAI API (Router not configured)")
            else:
                logger.warning("No LLM providers configured; falling back to deterministic responses")

        if self.test_mode:
            logger.info("Requesty client running in TEST_MODE; responses will be deterministic")

    # ------------------------------------------------------------------
    # Chat completions
    # ------------------------------------------------------------------
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        """Generate a chat completion synchronously."""
        target_model = model or self.default_chat_model

        if self.use_router and self.router_client:
            return self._router_chat_completion(messages, target_model, **kwargs)

        if self.openai_client:
            return self._openai_chat_completion(messages, target_model, **kwargs)

        return self._fallback_completion(messages, target_model, **kwargs)

    async def achat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        """Asynchronous helper for chat completions."""
        loop = asyncio.get_running_loop()
        func = functools.partial(self.chat_completion, messages, model=model, **kwargs)
        return await loop.run_in_executor(None, func)

    def _router_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        router_model = self._qualify_model(model)

        try:
            response = self.router_client.chat.completions.create(  # type: ignore[union-attr]
                model=router_model,
                messages=messages,
                temperature=kwargs.get("temperature", settings.PLANNING_TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", settings.PLANNING_MAX_TOKENS),
            )

            content = response.choices[0].message.content
            if response.usage:
                logger.info(
                    "Requesty Router usage - model=%s, prompt_tokens=%s, completion_tokens=%s",
                    router_model,
                    getattr(response.usage, "prompt_tokens", "?"),
                    getattr(response.usage, "completion_tokens", "?"),
                )
            return content
        except Exception as exc:
            logger.warning(f"Requesty Router request failed: {exc}")
            return self._fallback_completion(messages, model, **kwargs)

    def _openai_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        if not self.openai_client:
            raise RuntimeError("OpenAI API key not configured for fallback usage")

        response = self.openai_client.chat.completions.create(  # type: ignore[union-attr]
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", settings.TEMPERATURE),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        content = response.choices[0].message.content
        if response.usage:
            logger.info(
                "OpenAI usage - model=%s, total_tokens=%s",
                model,
                getattr(response.usage, "total_tokens", "?"),
            )
        return content

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def embed_texts(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        if not texts:
            return []

        target_model = model or self.default_embedding_model

        try:
            if self.use_router and self.router_client:
                router_model = self._qualify_model(target_model)
                response = self.router_client.embeddings.create(  # type: ignore[union-attr]
                    model=router_model,
                    input=texts,
                )
            elif self.openai_client:
                response = self.openai_client.embeddings.create(  # type: ignore[union-attr]
                    model=target_model,
                    input=texts,
                )
            else:
                raise RuntimeError("No embedding provider configured")

            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning(f"Embedding request failed ({exc}); using deterministic embeddings")
            return [self._deterministic_embedding(text) for text in texts]

    async def aembed_texts(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        loop = asyncio.get_running_loop()
        func = functools.partial(self.embed_texts, texts, model=model)
        return await loop.run_in_executor(None, func)

    # ------------------------------------------------------------------
    # Metadata & fallbacks
    # ------------------------------------------------------------------
    def get_usage_stats(self) -> Dict[str, Any]:
        if not self.use_router:
            return {"error": "Requesty Router not configured"}

        try:
            headers = {"Authorization": f"Bearer {self.router_api_key}"}
            response = requests.get("https://router.requesty.ai/v1/usage", headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"error": f"API request failed: {response.status_code}"}
        except Exception as exc:  # pragma: no cover - best effort logging
            return {"error": str(exc)}

    def _fallback_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        if self.openai_client:
            try:
                return self._openai_chat_completion(messages, model, **kwargs)
            except Exception as exc:
                logger.error(f"OpenAI fallback failed: {exc}")

        prompt_preview = messages[-1]["content"] if messages else ""

        if self.test_mode:
            payload = {
                "assistant_reply": (f"[Test reply] {prompt_preview[:160]}" if prompt_preview else "[Test reply] Ready to plan."),
                "actions": {"create_plan": False},
            }
            return json.dumps(payload)

        logger.warning("Returning deterministic fallback response (no LLM providers available)")
        return f"[Fallback response] Unable to reach LLM provider. Last prompt: {prompt_preview[:120]}"

    @staticmethod
    def _deterministic_embedding(text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [round(byte / 255.0, 6) for byte in digest[:32]]

    @staticmethod
    def _qualify_model(model: str) -> str:
        if "/" in model:
            return model
        if model.startswith("glm") or model.startswith("embedding"):
            return f"requesty/{model}"
        return f"openai/{model}"