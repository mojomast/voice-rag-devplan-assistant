import requests
from typing import Dict, Any, Optional, List
from loguru import logger
from openai import OpenAI
from .config import settings

class RequestyClient:
    """
    Requesty.ai client wrapper for intelligent LLM routing and cost optimization.
    Falls back to direct OpenAI if Requesty.ai is not configured.
    """

    def __init__(self):
        self.requesty_api_key = settings.REQUESTY_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.requesty.ai/v1"  # Adjust based on actual API

        # Fallback OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        self.use_requesty = bool(self.requesty_api_key)

        if self.use_requesty:
            logger.info("Requesty.ai client initialized - cost optimization enabled")
        else:
            logger.warning("Requesty.ai key not found - using direct OpenAI API")

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> str:
        """
        Generate chat completion using Requesty.ai smart routing or direct OpenAI.
        """
        if not model:
            model = settings.LLM_MODEL

        if self.use_requesty:
            return self._requesty_chat_completion(messages, model, **kwargs)
        else:
            return self._openai_chat_completion(messages, model, **kwargs)

    def _requesty_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Make a chat completion request through Requesty.ai"""
        try:
            headers = {
                "Authorization": f"Bearer {self.requesty_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", settings.TEMPERATURE),
                "max_tokens": kwargs.get("max_tokens", 2000),
                # Requesty.ai specific parameters for optimization
                "smart_routing": True,
                "cost_optimization": True,
                "fallback_models": ["gpt-3.5-turbo", "gpt-4o-mini"]
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Log cost optimization metrics if available
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(f"Requesty.ai usage - tokens: {usage.get('total_tokens', 'N/A')}, "
                              f"cost_saved: {usage.get('cost_saved', 'N/A')}")

                return content
            else:
                logger.warning(f"Requesty.ai request failed: {response.status_code}")
                return self._openai_chat_completion(messages, model, **kwargs)

        except Exception as e:
            logger.error(f"Requesty.ai request error: {e}")
            return self._openai_chat_completion(messages, model, **kwargs)

    def _openai_chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Fallback to direct OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get("temperature", settings.TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", 2000)
            )

            content = response.choices[0].message.content
            logger.info(f"OpenAI direct usage - model: {model}, tokens: {response.usage.total_tokens}")
            return content

        except Exception as e:
            logger.error(f"OpenAI direct request error: {e}")
            raise

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from Requesty.ai if available"""
        if not self.use_requesty:
            return {"error": "Requesty.ai not configured"}

        try:
            headers = {"Authorization": f"Bearer {self.requesty_api_key}"}
            response = requests.get(f"{self.base_url}/usage", headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API request failed: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}