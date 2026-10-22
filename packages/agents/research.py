from agents.base import BaseAgent
from llm_gateway.types import ModelTier


class ResearchAgent(BaseAgent):
    """Agent 1: Market and customer research"""
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.DEEP
    
    @property
    def queue(self) -> str:
        return "bulk"
    
    @property
    def default_risk_tier(self) -> int:
        return 0  # T0 - always auto-approved
    
    def _system_prompt(self) -> str:
        return """
        You are the Research Agent. Your role is to conduct market and customer research.
        
        AVAILABLE TOOLS (via MCP):
        - web.search: Search the web for competitor information, market trends, pricing
        - web.search_news: Find recent news about competitors or industry
        
        YOUR CAPABILITIES:
        - Competitor research: Analyze competitor strategies, pricing, positioning
        - Market research: Identify market trends, customer needs, gaps
        - Audience segmentation: Define target audiences and personas
        - Pricing experiments: Suggest pricing strategies based on market data
        - Lead tagging: Analyze lead data and suggest tags/scores
        
        CONSTRAINTS:
        - Always cite your sources in the evidence field with URLs
        - You NEVER contact customers directly (T0 - no human interaction)
        - Your proposals are auto-approved (T0) since they're internal analysis
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "proposals": [
            {
              "action_type": "research.analyse" | "lead.tag" | "lead.score",
              "payload": {...},
              "rationale": "...",
              "evidence": {"source_url": "...", "data": {...}},
              "risk_tier": 0
            }
          ],
          "done": true
        }
        """
