from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from llm_gateway.types import ModelTier
from llm_gateway.graph import build_agent_graph, run_agent_graph


@dataclass
class RunContext:
    """Immutable context passed to agents"""
    org_id: str
    goal: str
    lead: dict
    brand: dict
    conversation_history: str
    knowledge_base: str
    trust_level: int
    lead_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for LangGraph"""
        return {
            'org_id': self.org_id,
            'goal': self.goal,
            'lead': self.lead,
            'brand': self.brand,
            'conversation_history': self.conversation_history,
            'knowledge_base': self.knowledge_base,
            'trust_level': self.trust_level,
            'lead_id': self.lead_id,
        }


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self):
        import re
        # CamelCase -> snake_case: CustomerSuccessAgent -> customer_success
        raw = re.sub(r'(?<!^)(?=[A-Z])', '_', self.__class__.__name__).lower()
        self.name = raw.replace('_agent', '')
        self._compiled_graph = None
    
    @property
    @abstractmethod
    def model_tier(self) -> ModelTier:
        """Model tier for this agent"""
        pass
    
    @property
    @abstractmethod
    def queue(self) -> str:
        """Celery queue for this agent"""
        pass
    
    @property
    @abstractmethod
    def default_risk_tier(self) -> int:
        """Default risk tier (T0-T3)"""
        pass
    
    @abstractmethod
    def _system_prompt(self) -> str:
        """System prompt for this agent"""
        pass
    
    def run(self, ctx: RunContext) -> List[dict]:
        """
        Execute the agent with given context.
        Returns list of proposals.
        """
        graph = self._get_compiled_graph()
        proposals = run_agent_graph(graph, ctx.to_dict())
        
        # Tag proposals with agent name
        for p in proposals:
            p["agent"] = self.name
            if ctx.lead_id:
                p["lead_id"] = ctx.lead_id
            # Set default risk tier if not specified
            if "risk_tier" not in p:
                p["risk_tier"] = self.default_risk_tier
        
        return proposals
    
    def _get_compiled_graph(self):
        """Get or create compiled LangGraph (cached at class level)"""
        cache_attr = f"_compiled_graph_{self.name}"
        if not hasattr(self.__class__, cache_attr):
            graph = build_agent_graph(self.name, self._system_prompt(), self.model_tier)
            setattr(self.__class__, cache_attr, graph)
        return getattr(self.__class__, cache_attr)
