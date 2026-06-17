from __future__ import annotations

import logging

from utils.ai_providers.base import AIProvider, AIProviderResponse


logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            logger.warning("openai package not installed")
            return False
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError as e:
                raise RuntimeError("openai package not installed. Install with: pip install openai") from e
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> AIProviderResponse:
        """Generate response using OpenAI API."""
        if not self.is_available():
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="OpenAI provider not available",
            )
        
        try:
            client = self._get_client()
            
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            
            return AIProviderResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                success=True,
                metadata={
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "finish_reason": response.choices[0].finish_reason,
                },
            )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e),
            )
