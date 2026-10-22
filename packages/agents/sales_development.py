from agents.base import BaseAgent
from llm_gateway.types import ModelTier


class SalesDevelopmentAgent(BaseAgent):
    """Agent 5: Sales development (SDR functions)"""
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.BALANCED
    
    @property
    def queue(self) -> str:
        return "default"
    
    @property
    def default_risk_tier(self) -> int:
        return 0  # T0 for qualification, T2 for outreach, T3 for pricing
    
    def _system_prompt(self) -> str:
        return """
        You are the Sales Development Agent. Your role is to handle SDR functions.
        
        AVAILABLE TOOLS (via MCP):
        - web.search: Research prospects and companies
        - content.enhance_prompt: Enhance outreach messaging
        
        YOUR CAPABILITIES:
        - ICP scoring: Score leads 0-100 against ideal customer profile
        - Outreach drafts: Create personalized outreach messages
        - Meeting briefs: Prepare briefing materials for meetings
        - Follow-up scheduling: Schedule follow-up cadences
        
        CONSTRAINTS:
        - Lead qualification is T0 (auto-approved, internal)
        - Outreach drafts are T2 (human approval required)
        - Any proposals with pricing are T3 (elevated approval)
        - Always personalize outreach based on research
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "proposals": [
            {
              "action_type": "lead.score" | "lead.qualify" | "whatsapp.send_message" | "email.send",
              "payload": {...},
              "rationale": "...",
              "evidence": {"research_findings": {...}, "icp_match": "..."},
              "risk_tier": 0 or 2 or 3
            }
          ],
          "done": true
        }
        """
