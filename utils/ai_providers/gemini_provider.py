from __future__ import annotations

import logging

from utils.ai_providers.base import AIProvider, AIProviderResponse


logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import google.generativeai  # noqa: F401
            return True
        except ImportError:
            logger.warning("google-generativeai package not installed")
            return False
    
    def _get_client(self):
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError as e:
                raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai") from e
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> AIProviderResponse:
        """Generate response using Gemini API."""
        if not self.is_available():
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Gemini provider not available",
            )
        
        try:
            client = self._get_client()
            
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = client.generate_content(
                prompt,
                generation_config=generation_config,
            )
            
            content = response.text
            
            return AIProviderResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                success=True,
                metadata={
                    "usage": {
                        "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, "usage_metadata") else 0,
                        "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, "usage_metadata") else 0,
                    },
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                },
            )
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return AIProviderResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e),
            )
