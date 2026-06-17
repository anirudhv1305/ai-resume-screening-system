from __future__ import annotations

import logging

from utils.ai_providers.base import AIProvider, AIProviderResponse


logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "claude"
    
    def is_available(self) -> bool:
        """Check if Claude is configured."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            logger.warning("anthropic package not installed")
            return False
    
    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError as e:
                raise RuntimeError("anthropic package not installed. Install with: pip install anthropic") from e
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> AIProviderResponse:
        """Generate response using Claude API."""
        if not self.is_available():
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Claude provider not available",
            )
        
        try:
            client = self._get_client()
            
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            
            response = client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.content[0].text
            
            return AIProviderResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                success=True,
                metadata={
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "stop_reason": response.stop_reason,
                },
            )
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e),
            )
