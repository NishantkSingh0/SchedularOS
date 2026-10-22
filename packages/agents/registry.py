from typing import Dict
from agents.base import BaseAgent


_REGISTRY: Dict[str, BaseAgent] = {}


def register(agent: BaseAgent):
    """Register an agent in the global registry"""
    _REGISTRY[agent.name] = agent


def get_agent(name: str) -> BaseAgent:
    """Get an agent by name"""
    if name not in _REGISTRY:
        raise ValueError(f"Agent '{name}' not found in registry")
    return _REGISTRY[name]


def list_agents() -> list:
    """List all registered agent names"""
    return list(_REGISTRY.keys())


def _bootstrap():
    """Bootstrap the agent registry with all agents"""
    from agents.research import ResearchAgent
    from agents.creative import CreativeAgent
    from agents.paid_media import PaidMediaAgent
    from agents.partnerships import PartnershipsAgent
    from agents.sales_development import SalesDevelopmentAgent
    from agents.lead_generation import LeadGenerationAgent
    from agents.conversation import ConversationAgent
    from agents.followup import FollowupAgent
    from agents.conversion import ConversionAgent
    from agents.customer_success import CustomerSuccessAgent
    from agents.orchestrator import OrchestratorAgent
    
    # Register all agents as singletons
    register(ResearchAgent())
    register(CreativeAgent())
    register(PaidMediaAgent())
    register(PartnershipsAgent())
    register(SalesDevelopmentAgent())
    register(LeadGenerationAgent())
    register(ConversationAgent())
    register(FollowupAgent())
    register(ConversionAgent())
    register(CustomerSuccessAgent())
    register(OrchestratorAgent())


# Bootstrap on import
_bootstrap()
