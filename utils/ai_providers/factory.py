from __future__ import annotations

import logging
import os
from typing import Literal

from utils.ai_providers.base import AIProvider, AIProviderResponse
from utils.ai_providers.claude_provider import ClaudeProvider
from utils.ai_providers.gemini_provider import GeminiProvider
from utils.ai_providers.openai_provider import OpenAIProvider


logger = logging.getLogger(__name__)

ProviderType = Literal["openai", "claude", "gemini"]


class AIProviderFactory:
    """Factory for creating and managing AI providers with fallback support."""
    
    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize providers from environment variables."""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if openai_key:
            self._providers["openai"] = OpenAIProvider(openai_key, openai_model)
        
        # Claude
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        if claude_key:
            self._providers["claude"] = ClaudeProvider(claude_key, claude_model)
        
        # Gemini
        gemini_key = os.getenv("GOOGLE_API_KEY", "")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if gemini_key:
            self._providers["gemini"] = GeminiProvider(gemini_key, gemini_model)
    
    def get_provider(self, provider_name: ProviderType) -> AIProvider | None:
        """Get a specific provider by name."""
        provider = self._providers.get(provider_name)
        if provider and provider.is_available():
            return provider
        return None
    
    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return [
            name for name, provider in self._providers.items()
            if provider.is_available()
        ]
    
    def generate_with_fallback(
        self,
        prompt: str,
        preferred_provider: ProviderType | None = None,
        fallback_order: list[ProviderType] | None = None,
        **kwargs,
    ) -> AIProviderResponse:
        """
        Generate response with automatic fallback to other providers.
        
        Args:
            prompt: Text prompt for AI generation
            preferred_provider: Preferred provider to try first
            fallback_order: Custom fallback order (default: openai, claude, gemini)
            **kwargs: Additional parameters for generation (temperature, max_tokens)
        
        Returns:
            AIProviderResponse with content or error
        """
        if fallback_order is None:
            fallback_order = ["openai", "claude", "gemini"]
        
        # If preferred provider specified, try it first
        if preferred_provider:
            providers_to_try = [preferred_provider] + [
                p for p in fallback_order if p != preferred_provider
            ]
        else:
            providers_to_try = fallback_order
        
        tried_providers = []
        last_error = None
        
        for provider_name in providers_to_try:
            provider = self.get_provider(provider_name)
            
            if not provider:
                logger.debug(f"Provider {provider_name} not available, skipping")
                continue
            
            tried_providers.append(provider_name)
            logger.info(f"Attempting generation with {provider_name}")
            
            try:
                response = provider.generate(prompt, **kwargs)
                
                if response.success:
                    logger.info(f"Successfully generated with {provider_name}")
                    return response
                else:
                    logger.warning(f"{provider_name} failed: {response.error}")
                    last_error = response.error
            
            except Exception as e:
                logger.error(f"Exception with {provider_name}: {e}")
                last_error = str(e)
        
        # All providers failed
        error_msg = (
            f"All AI providers failed. Tried: {', '.join(tried_providers)}. "
            f"Last error: {last_error or 'Unknown'}"
        )
        logger.error(error_msg)
        
        return AIProviderResponse(
            content="",
            provider="none",
            model="",
            success=False,
            error=error_msg,
            metadata={"tried_providers": tried_providers},
        )


# Singleton instance
_factory_instance: AIProviderFactory | None = None


def get_ai_provider_factory() -> AIProviderFactory:
    """Get singleton AIProviderFactory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AIProviderFactory()
    return _factory_instance
