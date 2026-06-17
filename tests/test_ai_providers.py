from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from utils.ai_providers.base import AIProviderResponse
from utils.ai_providers.claude_provider import ClaudeProvider
from utils.ai_providers.factory import AIProviderFactory
from utils.ai_providers.gemini_provider import GeminiProvider
from utils.ai_providers.openai_provider import OpenAIProvider


class MockOpenAIClient:
    """Mock OpenAI client."""
    
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.chat = self
        self.completions = self
    
    def create(self, **kwargs):
        if self.fail:
            raise Exception("OpenAI API error")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        return mock_response


class MockClaudeClient:
    """Mock Claude client."""
    
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.messages = self
    
    def create(self, **kwargs):
        if self.fail:
            raise Exception("Claude API error")
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude response"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        return mock_response


class MockGeminiClient:
    """Mock Gemini client."""
    
    def __init__(self, fail: bool = False):
        self.fail = fail
    
    def generate_content(self, prompt, **kwargs):
        if self.fail:
            raise Exception("Gemini API error")
        
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].finish_reason.name = "STOP"
        return mock_response


class OpenAIProviderTests(unittest.TestCase):
    
    def test_provider_name(self):
        provider = OpenAIProvider(api_key="test-key")
        self.assertEqual(provider.provider_name, "openai")
    
    def test_is_available_no_key(self):
        provider = OpenAIProvider(api_key="")
        self.assertFalse(provider.is_available())
    
    @patch("utils.ai_providers.openai_provider.OpenAIProvider.is_available", return_value=True)
    def test_successful_generation(self, mock_available):
        mock_client = MockOpenAIClient()
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        provider._client = mock_client
        
        response = provider.generate("Test prompt")
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "OpenAI response")
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.model, "gpt-4o-mini")
        self.assertIn("usage", response.metadata)
    
    @patch("utils.ai_providers.openai_provider.OpenAIProvider.is_available", return_value=True)
    def test_failed_generation(self, mock_available):
        mock_client = MockOpenAIClient(fail=True)
        provider = OpenAIProvider(api_key="test-key")
        provider._client = mock_client
        
        response = provider.generate("Test prompt")
        
        self.assertFalse(response.success)
        self.assertIn("api", response.error.lower())


class ClaudeProviderTests(unittest.TestCase):
    
    def test_provider_name(self):
        provider = ClaudeProvider(api_key="test-key")
        self.assertEqual(provider.provider_name, "claude")
    
    def test_is_available_no_key(self):
        provider = ClaudeProvider(api_key="")
        self.assertFalse(provider.is_available())
    
    @patch("utils.ai_providers.claude_provider.ClaudeProvider.is_available", return_value=True)
    def test_successful_generation(self, mock_available):
        mock_client = MockClaudeClient()
        provider = ClaudeProvider(api_key="test-key", model="claude-3-5-sonnet-20241022")
        provider._client = mock_client
        
        response = provider.generate("Test prompt")
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Claude response")
        self.assertEqual(response.provider, "claude")
        self.assertEqual(response.model, "claude-3-5-sonnet-20241022")
        self.assertIn("usage", response.metadata)
    
    @patch("utils.ai_providers.claude_provider.ClaudeProvider.is_available", return_value=True)
    def test_failed_generation(self, mock_available):
        mock_client = MockClaudeClient(fail=True)
        provider = ClaudeProvider(api_key="test-key")
        provider._client = mock_client
        
        response = provider.generate("Test prompt")
        
        self.assertFalse(response.success)
        self.assertIn("api", response.error.lower())


class GeminiProviderTests(unittest.TestCase):
    
    def test_provider_name(self):
        provider = GeminiProvider(api_key="test-key")
        self.assertEqual(provider.provider_name, "gemini")
    
    def test_is_available_no_key(self):
        provider = GeminiProvider(api_key="")
        self.assertFalse(provider.is_available())
    
    @patch("utils.ai_providers.gemini_provider.GeminiProvider.is_available", return_value=True)
    def test_successful_generation(self, mock_available):
        mock_model = MockGeminiClient()
        provider = GeminiProvider(api_key="test-key", model="gemini-1.5-flash")
        provider._client = mock_model
        
        response = provider.generate("Test prompt")
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Gemini response")
        self.assertEqual(response.provider, "gemini")
        self.assertEqual(response.model, "gemini-1.5-flash")
        self.assertIn("usage", response.metadata)
    
    @patch("utils.ai_providers.gemini_provider.GeminiProvider.is_available", return_value=True)
    def test_failed_generation(self, mock_available):
        mock_model = MockGeminiClient(fail=True)
        provider = GeminiProvider(api_key="test-key")
        provider._client = mock_model
        
        response = provider.generate("Test prompt")
        
        self.assertFalse(response.success)
        self.assertIn("api", response.error.lower())


class AIProviderFactoryTests(unittest.TestCase):
    
    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-claude-key",
        "GOOGLE_API_KEY": "test-gemini-key",
    })
    def test_factory_initialization(self):
        factory = AIProviderFactory()
        
        # Should have all three providers configured
        self.assertIn("openai", factory._providers)
        self.assertIn("claude", factory._providers)
        self.assertIn("gemini", factory._providers)
    
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("utils.ai_providers.openai_provider.OpenAIProvider.is_available", return_value=True)
    def test_get_provider(self, mock_available):
        factory = AIProviderFactory()
        provider = factory.get_provider("openai")
        
        self.assertIsNotNone(provider)
        self.assertEqual(provider.provider_name, "openai")
    
    @patch.dict("os.environ", {})
    def test_get_provider_unavailable(self):
        factory = AIProviderFactory()
        provider = factory.get_provider("openai")
        
        self.assertIsNone(provider)
    
    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "ANTHROPIC_API_KEY": "test-key",
    })
    def test_get_available_providers(self):
        factory = AIProviderFactory()
        available = factory.get_available_providers()
        
        # Should have at least the configured providers
        self.assertIsInstance(available, list)
    
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("utils.ai_providers.openai_provider.OpenAIProvider.is_available", return_value=True)
    def test_fallback_chain_success_first(self, mock_available):
        mock_client = MockOpenAIClient()
        
        factory = AIProviderFactory()
        # Inject mock client
        factory._providers["openai"]._client = mock_client
        
        response = factory.generate_with_fallback(
            "Test prompt",
            preferred_provider="openai"
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.content, "OpenAI response")
    
    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "ANTHROPIC_API_KEY": "test-key",
    })
    @patch("utils.ai_providers.openai_provider.OpenAIProvider.is_available", return_value=True)
    @patch("utils.ai_providers.claude_provider.ClaudeProvider.is_available", return_value=True)
    def test_fallback_chain_openai_fails_claude_succeeds(
        self, mock_claude_available, mock_openai_available
    ):
        factory = AIProviderFactory()
        
        # OpenAI fails
        mock_openai_client = MockOpenAIClient(fail=True)
        factory._providers["openai"]._client = mock_openai_client
        
        # Claude succeeds
        mock_claude_client = MockClaudeClient()
        factory._providers["claude"]._client = mock_claude_client
        
        response = factory.generate_with_fallback(
            "Test prompt",
            fallback_order=["openai", "claude"]
        )
        
        # Should fallback to Claude
        self.assertTrue(response.success)
        self.assertEqual(response.provider, "claude")
        self.assertEqual(response.content, "Claude response")
    
    @patch.dict("os.environ", {})
    def test_fallback_chain_all_fail(self):
        factory = AIProviderFactory()
        response = factory.generate_with_fallback("Test prompt")
        
        self.assertFalse(response.success)
        self.assertIn("all ai providers failed", response.error.lower())
    
    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "ANTHROPIC_API_KEY": "test-key",
    })
    @patch("utils.ai_providers.claude_provider.ClaudeProvider.is_available", return_value=True)
    def test_custom_fallback_order(self, mock_claude_available):
        factory = AIProviderFactory()
        
        # Claude succeeds
        mock_claude_client = MockClaudeClient()
        factory._providers["claude"]._client = mock_claude_client
        
        response = factory.generate_with_fallback(
            "Test prompt",
            fallback_order=["claude", "openai"]  # Try Claude first
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.provider, "claude")


class AIProviderResponseTests(unittest.TestCase):
    
    def test_response_to_dict(self):
        response = AIProviderResponse(
            content="Test content",
            provider="openai",
            model="gpt-4o-mini",
            success=True,
            metadata={"tokens": 100},
        )
        
        result = response.to_dict()
        
        self.assertEqual(result["content"], "Test content")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-4o-mini")
        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["tokens"], 100)
    
    def test_response_with_error(self):
        response = AIProviderResponse(
            content="",
            provider="openai",
            model="gpt-4o-mini",
            success=False,
            error="API error",
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.error, "API error")


if __name__ == "__main__":
    unittest.main()
