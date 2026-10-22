from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Any


class ModelTier(Enum):
    """Model tiers for different use cases"""
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"
    DECISION = "decision"


@dataclass
class LLMMessage:
    """LLM message wrapper"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMRequest:
    """LLM request wrapper"""
    messages: List[LLMMessage]
    tier: ModelTier
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    org_id: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response wrapper"""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cached: bool = False
