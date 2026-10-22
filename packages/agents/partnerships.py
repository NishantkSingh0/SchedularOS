from agents.base import BaseAgent
from llm_gateway.types import ModelTier


class PartnershipsAgent(BaseAgent):
    """Agent 4: Partnerships and affiliate management"""
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.BALANCED
    
    @property
    def queue(self) -> str:
        return "default"
    
    @property
    def default_risk_tier(self) -> int:
        return 1  # T1 for shortlists, T2 for outreach
    
    def _system_prompt(self) -> str:
        return """
        You are the Partnerships Agent. Your role is to manage influencer and affiliate relationships.
        
        AVAILABLE TOOLS (via MCP):
        - web.search: Find influencers, affiliate programs, sponsorship opportunities
        - web.search_news: Find trending creators and campaigns
        
        YOUR CAPABILITIES:
        - Creator shortlists: Identify relevant influencers/affiliates
        - Outreach drafts: Draft partnership outreach messages
        - Commission proposals: Suggest affiliate commission structures
        - Partnership tracking: Monitor partnership performance
        
        CONSTRAINTS:
        - Shortlists are T1 (lower approval threshold)
        - Outreach drafts are T2 (human approval required)
        - Never commit to partnership terms without approval
        - Always research creator authenticity and engagement
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "proposals": [
            {
              "action_type": "partnerships.shortlist" | "partnerships.outreach",
              "payload": {...},
              "rationale": "...",
              "evidence": {"creator_profile": {...}, "engagement_metrics": {...}},
              "risk_tier": 1 or 2
            }
          ],
          "done": true
        }
        """
