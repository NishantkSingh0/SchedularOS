from agents.base import BaseAgent
from llm_gateway.types import ModelTier, LLMRequest, LLMMessage
from llm_gateway.client import complete_json


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Decomposes goals into agent steps.
    This agent does NOT run via LangGraph - it has a special plan() method.
    """
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.DEEP
    
    @property
    def queue(self) -> str:
        return "default"
    
    @property
    def default_risk_tier(self) -> int:
        return 0  # T0 - internal planning
    
    def _system_prompt(self) -> str:
        return """
        You are the Orchestrator Agent. Your role is to decompose goals into executable agent steps.
        
        AVAILABLE AGENTS:
        - research: Market research, competitor analysis, lead scoring
        - creative: Content creation, copywriting, creative briefs
        - paid_media: Campaign management, budget optimization
        - partnerships: Influencer/affiliate management
        - sales_development: SDR functions, outreach, ICP scoring
        - lead_generation: Lead infrastructure, funnel analysis
        - conversation: Sales conversations, inbound replies
        - followup: Follow-up cadence management
        - conversion: Conversion optimization, A/B tests
        - customer_success: Support, retention, upselling
        
        YOUR TASK:
        Given a goal, decompose it into a sequence of agent steps.
        Each step should specify:
        - agent: Which agent to run
        - delay_minutes: How long to wait before running this step (0 for immediate)
        
        CONSTRAINTS:
        - Only use agents from the available list
        - Steps should be in logical order
        - Be specific about timing (0 for immediate, positive numbers for delays)
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "steps": [
            {"agent": "research", "delay_minutes": 0},
            {"agent": "creative", "delay_minutes": 0},
            {"agent": "paid_media", "delay_minutes": 10}
          ],
          "context": {"goal_type": "...", "estimated_duration": "..."}
        }
        """
    
    def plan(self, goal: str, org_id: str) -> dict:
        """
        Decompose a goal into agent steps.
        Returns dict with 'steps' list and 'context'.
        """
        system_prompt = self._system_prompt()
        
        user_content = f"""
        GOAL: {goal}
        
        Decompose this goal into a sequence of agent steps.
        Only use agents from the available list.
        """
        
        result = complete_json(LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_content)
            ],
            tier=ModelTier.DEEP,
            temperature=0.2,
            org_id=org_id
        ))
        
        # Validate agent names
        from agents.registry import list_agents
        valid_agents = set(list_agents())
        
        for step in result.get("steps", []):
            if step["agent"] not in valid_agents:
                raise ValueError(f"Invalid agent '{step['agent']}'. Valid agents: {valid_agents}")
        
        return result
    
    def run(self, ctx) -> list:
        """Orchestrator does not run via LangGraph - use plan() instead"""
        raise NotImplementedError("Orchestrator does not use run(). Use plan() instead.")
