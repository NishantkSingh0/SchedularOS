"""
LLM Gateway (compatibility shim)
Delegates to llm_gateway.client.LLMGateway — the single real gateway with
provider fallback (Jev -> OpenAI), Redis caching and model tiers.
"""
import os
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass

from llm_gateway.types import LLMRequest, ModelTier
from llm_gateway.client import get_llm_gateway as _get_client_gateway


class LLMProvider(Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    JEV = "jev"
    ANTHROPIC = "anthropic"


@dataclass
class LLMMessage:
    """Represents a message in the conversation"""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class LLMResponse:
    """Represents an LLM response"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None


class LLMGateway:
    """Gateway for LLM API calls — delegates to llm_gateway.client"""

    def __init__(self, default_provider: LLMProvider = LLMProvider.OPENAI):
        self.default_provider = default_provider

    def generate(
        self,
        messages: List[LLMMessage],
        provider: Optional[LLMProvider] = None,
        fallback_providers: Optional[List[LLMProvider]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text using the shared client gateway (Jev -> OpenAI fallback)."""
        from llm_gateway.types import LLMMessage as ClientMessage

        request = LLMRequest(
            messages=[ClientMessage(role=m.role, content=m.content) for m in messages],
            tier=kwargs.pop("tier", ModelTier.BALANCED),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
        )
        resp = _get_client_gateway().complete(request)
        return LLMResponse(
            content=resp.content,
            provider="jev" if _get_client_gateway().use_jev else "openai",
            model=resp.model,
            tokens_used=resp.prompt_tokens + resp.completion_tokens,
        )


# Singleton instance
_llm_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """Get or create the LLM gateway singleton"""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    return _llm_gateway
