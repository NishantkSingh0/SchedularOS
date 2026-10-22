from dataclasses import dataclass
from typing import Optional
from core.models import Lead, Brand, AgentTrustState, Conversation, Message, KnowledgeDocument
from memory.retrieval import retrieve_relevant_docs, build_knowledge_context


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


def build_run_context(step) -> RunContext:
    """
    Build the complete context for an agent run.
    Queries: Lead, last 20 Messages, Brand, AgentTrustState, KnowledgeDocument
    Returns: immutable RunContext dataclass
    """
    run = step.run
    org_id = str(run.org.id)
    
    # Get lead info
    lead_data = {}
    lead_id = None
    if run.lead:
        lead_id = str(run.lead.id)
        lead_data = {
            "name": run.lead.name,
            "email": run.lead.email,
            "phone": run.lead.phone,
            "stage": run.lead.stage,
            "score": run.lead.score,
            "tags": run.lead.tags,
            "has_whatsapp_consent": run.lead.has_whatsapp_consent,
            "has_email_consent": run.lead.has_email_consent,
            "last_contacted_at": run.lead.last_contacted_at.isoformat() if run.lead.last_contacted_at else None,
        }
        
        # Get conversation history (last 20 messages)
        conversation_history = ""
        if run.lead:
            conversation = Conversation.objects.filter(
                lead=run.lead
            ).order_by('-created_at').first()
            
            if conversation:
                messages = Message.objects.filter(
                    conversation=conversation
                ).order_by('-created_at')[:20]
                
                for msg in reversed(messages):
                    direction = "→" if msg.direction == "outbound" else "←"
                    conversation_history += f"{direction} {msg.body}\n"
    else:
        conversation_history = "No lead specified."
    
    # Get brand info
    brand_data = {}
    if run.brand:
        brand_data = {
            "name": run.brand.name,
            "voice": run.brand.voice,
            "rules": run.brand.rules,
            "colors": run.brand.colors,
            "logo_url": run.brand.logo_url,
        }
    else:
        # Try to get default brand
        brand = Brand.objects.filter(org=run.org).first()
        if brand:
            brand_data = {
                "name": brand.name,
                "voice": brand.voice,
                "rules": brand.rules,
                "colors": brand.colors,
                "logo_url": brand.logo_url,
            }
    
    # Get trust level (wildcard row if present, else the agent's max earned level)
    trust_state = AgentTrustState.objects.filter(
        org=run.org,
        agent=step.agent
    ).order_by('-trust_level').first()
    trust_level = trust_state.trust_level if trust_state else 1  # Default L1
    
    # Get knowledge base (RAG)
    knowledge_base = ""
    if run.goal:
        try:
            docs = retrieve_relevant_docs(
                org_id=org_id,
                query=run.goal,
                limit=3
            )
            knowledge_base = build_knowledge_context(docs)
        except:
            knowledge_base = "Knowledge base not available."
    
    return RunContext(
        org_id=org_id,
        goal=run.goal,
        lead=lead_data,
        brand=brand_data,
        conversation_history=conversation_history,
        knowledge_base=knowledge_base,
        trust_level=trust_level,
        lead_id=lead_id
    )
