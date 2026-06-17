from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProviderResponse:
    """Standardized response format for all AI providers."""
    
    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        success: bool = True,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.success = success
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> AIProviderResponse:
        """Generate AI response from prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass
