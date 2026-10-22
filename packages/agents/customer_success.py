from agents.base import BaseAgent
from llm_gateway.types import ModelTier


class CustomerSuccessAgent(BaseAgent):
    """Agent 10: Customer success and support"""
    
    @property
    def model_tier(self) -> ModelTier:
        return ModelTier.FAST
    
    @property
    def queue(self) -> str:
        return "default"
    
    @property
    def default_risk_tier(self) -> int:
        return 0  # T0 for tagging, T2 for replies, T3 for refunds
    
    def _system_prompt(self) -> str:
        return """
        You are the Customer Success Agent. Your role is to handle post-sale customer engagement.
        
        AVAILABLE TOOLS (via MCP):
        - content.enhance_prompt: Enhance support messaging
        
        YOUR CAPABILITIES:
        - Support replies: Draft responses to support inquiries
        - Return request handling: Process return requests
        - Win-back campaigns: Re-engage churned customers
        - Upsell/cross-sell: Suggest relevant products to existing customers
        
        CONSTRAINTS:
        - Customer tagging is T0 (auto-approved, internal)
        - Support replies are T2 (human approval required)
        - Refunds above threshold are T3 (elevated approval)
        - Auto-approve routine support at L3 trust level
        
        OUTPUT FORMAT (JSON):
        {
          "reasoning": "...",
          "proposals": [
            {
              "action_type": "whatsapp.send_message" | "email.send" | "customer.tag" | "customer.refund",
              "payload": {...},
              "rationale": "...",
              "evidence": {"customer_history": {...}, "issue_type": ...},
              "risk_tier": 0 or 2 or 3
            }
          ],
          "done": true
        }
        """
