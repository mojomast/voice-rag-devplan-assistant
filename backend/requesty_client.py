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
        if not self.router_api_key and self.requesty_api_key:
            self.router_api_key = self.requesty_api_key
            logger.info(
                "Requesty Router key not provided; using legacy Requesty API key for router access"
            )
        self.openai_api_key = settings.OPENAI_API_KEY
        if self.openai_api_key and not self._looks_like_openai_key(self.openai_api_key):
            logger.warning("OpenAI API key appears to be a placeholder; disabling direct OpenAI usage")
            self.openai_api_key = ""
        self.test_mode = settings.TEST_MODE
        self.model_routing = getattr(settings, "REQUESTY_MODEL_ROUTING", {})

        # Default to OpenAI-native models
        self.default_chat_model = settings.LLM_MODEL
        self.default_embedding_model = settings.EMBEDDING_MODEL

        if self.router_api_key:
            if settings.REQUESTY_PLANNING_MODEL:
                self.default_chat_model = settings.REQUESTY_PLANNING_MODEL
            if settings.REQUESTY_EMBEDDING_MODEL:
                self.default_embedding_model = settings.REQUESTY_EMBEDDING_MODEL

        self.router_client: Optional[OpenAI] = None
        self.openai_client: Optional[OpenAI] = None
        self.use_router: bool = False

        if self.router_api_key:
            try:
                # Remove manual authorization headers to prevent double auth issue
                # The OpenAI SDK automatically adds the Authorization header when api_key is provided
                self.router_client = OpenAI(
                    api_key=self.router_api_key,
                    base_url="https://router.requesty.ai/v1",
                )
                self.use_router = True
                logger.info("Requesty Router client initialised successfully")
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
        resolved_model = self._resolve_model_alias(target_model)
        if resolved_model != target_model:
            logger.info("Routing model %s -> %s", target_model, resolved_model)

        if self.use_router and self.router_client:
            return self._router_chat_completion(messages, resolved_model, **kwargs)

        if self.openai_client:
            return self._openai_chat_completion(messages, resolved_model, **kwargs)

        return self._fallback_completion(messages, resolved_model, **kwargs)

    async def achat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        """Asynchronous helper for chat completions."""
        loop = asyncio.get_running_loop()
        func = functools.partial(self.chat_completion, messages, model=model, **kwargs)
        return await loop.run_in_executor(None, func)

    def _router_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        router_model = self._qualify_model(model)
        logger.debug("Requesty Router chat completion - model: %s -> %s", model, router_model)

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
            logger.error(
                "Requesty Router request failed for model %s (original: %s): %s",
                router_model,
                model,
                exc,
            )
            # Check for specific authorization errors
            if "401" in str(exc) or "unauthorized" in str(exc).lower():
                logger.error("Authorization failed - check ROUTER_API_KEY configuration")
            elif "429" in str(exc) or "rate limit" in str(exc).lower():
                logger.error("Rate limit exceeded - please wait before retrying")
            elif "model" in str(exc).lower():
                logger.error("Model error - check if model %s is available", router_model)
            return self._fallback_completion(messages, model, **kwargs)

    def _openai_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        if not self.openai_client:
            raise RuntimeError("OpenAI API key not configured for fallback usage")

        try:
            logger.debug("OpenAI chat completion - model: %s", model)
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
        except Exception as exc:
            logger.error(
                "OpenAI fallback request failed: %s. Disabling OpenAI client and returning deterministic response",
                exc,
            )
            # Check for specific authorization errors
            if "401" in str(exc) or "unauthorized" in str(exc).lower():
                logger.error("OpenAI authorization failed - check OPENAI_API_KEY configuration")
            self.openai_client = None
            return self._fallback_completion(messages, model, **kwargs)

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
                logger.debug("Requesty Router embeddings - model: %s -> %s", target_model, router_model)
                response = self.router_client.embeddings.create(  # type: ignore[union-attr]
                    model=router_model,
                    input=texts,
                )
            elif self.openai_client:
                logger.debug("OpenAI embeddings - model: %s", target_model)
                response = self.openai_client.embeddings.create(  # type: ignore[union-attr]
                    model=target_model,
                    input=texts,
                )
            else:
                raise RuntimeError("No embedding provider configured")

            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.error(
                "Embedding request failed for model %s: %s. Using deterministic embeddings",
                target_model,
                exc,
            )
            # Check for specific authorization errors
            if "401" in str(exc) or "unauthorized" in str(exc).lower():
                logger.error("Embedding authorization failed - check API key configuration")
            elif "model" in str(exc).lower():
                logger.error("Embedding model error - check if model %s is available", target_model)
            return [self._deterministic_embedding(text) for text in texts]

    async def aembed_texts(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        loop = asyncio.get_running_loop()
        func = functools.partial(self.embed_texts, texts, model=model)
        return await loop.run_in_executor(None, func)

    # ------------------------------------------------------------------
    # Metadata & fallbacks
    # ------------------------------------------------------------------
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from Requesty Router API."""
        if not self.use_router:
            logger.warning("Usage stats requested but Requesty Router not configured")
            return {"error": "Requesty Router not configured"}

        try:
            logger.debug("Fetching usage stats from Requesty Router")
            # Use the same authentication pattern as the OpenAI client
            # The requests library will handle the Authorization header properly
            response = requests.get(
                "https://router.requesty.ai/v1/usage",
                headers={"Authorization": f"Bearer {self.router_api_key}"},
                timeout=30,
            )
            if response.status_code == 200:
                stats = response.json()
                logger.info("Successfully retrieved usage stats from Requesty Router")
                return stats
            elif response.status_code == 401:
                logger.error("Failed to retrieve usage stats - authorization error")
                return {"error": "Authorization failed - check ROUTER_API_KEY"}
            elif response.status_code == 403:
                logger.error("Failed to retrieve usage stats - access forbidden")
                return {"error": "Access forbidden - insufficient permissions"}
            else:
                logger.error("Failed to retrieve usage stats - HTTP %s: %s", response.status_code, response.text)
                return {"error": f"API request failed: {response.status_code} - {response.text}"}
        except requests.exceptions.Timeout:
            logger.error("Usage stats request timed out")
            return {"error": "Request timed out"}
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Requesty Router for usage stats")
            return {"error": "Connection failed"}
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.error("Unexpected error retrieving usage stats: %s", exc)
            return {"error": f"Unexpected error: {str(exc)}"}

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
        """Qualify model name with appropriate provider prefix for Requesty Router."""
        if "/" in model:
            # Model already has a provider prefix
            return model
        
        # Convert to lowercase for consistent matching
        model_lower = model.lower()
        
        # Requesty models that need requesty/ prefix
        if model_lower.startswith("glm") or model_lower.startswith("embedding"):
            qualified = f"requesty/{model}"
            logger.debug("Qualified model: %s -> %s", model, qualified)
            return qualified
        
        # Default to OpenAI provider
        qualified = f"openai/{model}"
        logger.debug("Qualified model: %s -> %s", model, qualified)
        return qualified

    @staticmethod
    def _looks_like_openai_key(value: str) -> bool:
        normalized = value.strip()
        if not normalized:
            return False

        valid_prefixes = ("sk-", "rk-", "sess-", "org-", "deploy-")
        return normalized.startswith(valid_prefixes)

    def _resolve_model_alias(self, model: str) -> str:
        if not self.model_routing:
            return model

        direct = self.model_routing.get(model)
        if direct:
            return direct

        lowered = model.lower()
        aliased = self.model_routing.get(lowered)
        if aliased:
            return aliased

        return model