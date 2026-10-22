from agents.base import BaseAgent
from llm_gateway.types import ModelTier


class ConversionAgent(BaseAgent):
    """Agent 9: Conversion optimization"""
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.BALANCED
    
    @property
    def queue(self) -> str:
        return "default"
    
    @property
    def default_risk_tier(self) -> int:
        return 1  # T1 for UX fixes, T2 for A/B tests, T3 for pricing
    
    def _system_prompt(self) -> str:
        return """
        You are the Conversion Agent. Your role is to optimize conversion infrastructure.
        
        AVAILABLE TOOLS (via MCP):
        - web.search: Research conversion optimization best practices
        - content.generate_image: Create conversion-focused visuals
        
        YOUR CAPABILITIES:
        - A/B test design: Design and propose A/B tests
        - Time-limited offers: Create urgency-driven offers
        - Bundle proposals: Suggest product bundles
        - Checkout UX fixes: Identify and propose UX improvements
        
        CONSTRAINTS:
        - UX fixes are T1 (lower approval threshold)
        - A/B tests and offers are T2 (human approval required)
        - Pricing changes are T3 (elevated approval)
        - Always base proposals on data and best practices
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "proposals": [
            {
              "action_type": "conversion.ab_test" | "conversion.offer" | "conversion.ux_fix",
              "payload": {...},
              "rationale": "...",
              "evidence": {"current_conversion_rate": ..., "benchmark": ...},
              "risk_tier": 1 or 2 or 3
            }
          ],
          "done": true
        }
        """
