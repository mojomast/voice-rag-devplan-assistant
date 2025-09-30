import requests
from typing import Dict, Any, Optional, List
from loguru import logger
from openai import OpenAI

try:
    from .config import settings
except ImportError:  # pragma: no cover - enables direct module imports in tests
    from config import settings

class RequestyClient:
    """
    Requesty.ai Router client wrapper for intelligent LLM routing and cost optimization.
    Falls back to direct OpenAI if Requesty Router is not configured.
    """

    def __init__(self):
        self.router_api_key = settings.ROUTER_API_KEY
        self.requesty_api_key = settings.REQUESTY_API_KEY  # Legacy fallback
        self.openai_api_key = settings.OPENAI_API_KEY
        
        # Priority: ROUTER_API_KEY > REQUESTY_API_KEY > OPENAI_API_KEY
        self.router_client = None
        self.openai_client = None
        
        # Try to initialize Requesty Router client first
        if self.router_api_key:
            try:
                self.router_client = OpenAI(
                    api_key=self.router_api_key,
                    base_url="https://router.requesty.ai/v1",
                    default_headers={"Authorization": f"Bearer {self.router_api_key}"}
                )
                self.use_router = True
                logger.info("Requesty Router client initialized - cost optimization enabled")
            except Exception as exc:
                logger.warning(f"Failed to initialize Requesty Router client: {exc}")
                self.use_router = False
        else:
            self.use_router = False
        
        # Fallback OpenAI client
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Failed to initialize OpenAI fallback client: {exc}")
        
        if not self.use_router:
            if self.openai_client:
                logger.info("Using direct OpenAI API (Router not configured)")
            else:
                logger.warning("No LLM providers configured")

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> str:
        """
        Generate chat completion using Requesty Router smart routing or direct OpenAI.
        """
        if not model:
            model = settings.LLM_MODEL

        if self.use_router:
            return self._router_chat_completion(messages, model, **kwargs)
        else:
            return self._openai_chat_completion(messages, model, **kwargs)

    def _router_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Make a chat completion request through Requesty Router using OpenAI SDK"""
        try:
            # Requesty Router expects model format like "openai/gpt-4o-mini"
            # If model doesn't have a provider prefix, add "openai/"
            if "/" not in model:
                router_model = f"openai/{model}"
            else:
                router_model = model
            
            response = self.router_client.chat.completions.create(
                model=router_model,
                messages=messages,
                temperature=kwargs.get("temperature", settings.TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", 2000)
            )

            content = response.choices[0].message.content
            
            # Log usage metrics
            if response.usage:
                logger.info(f"Requesty Router usage - model: {router_model}, "
                          f"tokens: {response.usage.total_tokens}")
            
            return content

        except Exception as e:
            logger.warning(f"Requesty Router request failed: {e}")
            return self._fallback_completion(messages, model, **kwargs)

    def _openai_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Fallback to direct OpenAI API"""
        if not self.openai_client:
            raise RuntimeError("OpenAI API key not configured for fallback usage")

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", settings.TEMPERATURE),
            max_tokens=kwargs.get("max_tokens", 2000)
        )

        content = response.choices[0].message.content
        logger.info(f"OpenAI direct usage - model: {model}, tokens: {response.usage.total_tokens}")
        return content

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from Requesty Router if available"""
        if not self.use_router:
            return {"error": "Requesty Router not configured"}

        try:
            headers = {"Authorization": f"Bearer {self.router_api_key}"}
            response = requests.get("https://router.requesty.ai/v1/usage", headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API request failed: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def _fallback_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Provide a graceful fallback when Requesty and OpenAI are unavailable."""
        if self.openai_client:
            try:
                return self._openai_chat_completion(messages, model, **kwargs)
            except Exception as exc:
                logger.error(f"OpenAI fallback failed: {exc}")

        # Deterministic offline response to keep pipeline alive
        prompt_preview = messages[-1]["content"] if messages else ""
        logger.warning("Returning deterministic fallback response (no LLM providers available)")
        return f"[Fallback response] Unable to reach LLM provider. Last prompt: {prompt_preview[:120]}"