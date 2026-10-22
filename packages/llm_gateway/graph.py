from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from operator import add
from llm_gateway.types import LLMRequest, LLMMessage, ModelTier
from llm_gateway.client import complete_json


class AgentState(TypedDict):
    """State for agent execution in LangGraph"""
    messages: Annotated[List, add_messages]  # Append-only message history
    proposals: List[dict]                     # Accumulated proposals
    context: dict                            # RunContext snapshot
    iteration: int                           # Safety counter - max 5
    done: bool                               # LLM sets this to break loop
    error: Optional[str]                     # Set on unhandled exception


def build_agent_graph(agent_name: str, system_prompt: str, model_tier: ModelTier = ModelTier.BALANCED):
    """
    Builds a LangGraph StateGraph for any agent.
    All agents share the same topology: START → reason → should_continue → (loop or END)
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("reason", make_reason_node(agent_name, system_prompt, model_tier))
    graph.add_node("should_continue", should_continue_node)
    
    # Add edges
    graph.set_entry_point("reason")
    graph.add_edge("reason", "should_continue")
    graph.add_conditional_edges(
        "should_continue",
        lambda state: "end" if state.get("done") else "continue",
        {
            "continue": "reason",
            "end": END
        }
    )
    
    return graph.compile()


def make_reason_node(agent_name: str, system_prompt: str, model_tier: ModelTier = ModelTier.BALANCED):
    """
    The reasoning node that calls the LLM with the agent's context.
    """
    def reason_node(state: AgentState) -> dict:
        # Safety break
        if state["iteration"] >= 5:
            return {"done": True, "error": "Max iterations reached"}
        
        # Build user message from context
        ctx = state["context"]
        user_content = f"""
GOAL: {ctx.get('goal', '')}
LEAD: {ctx.get('lead', {}).get('name', 'N/A')} | Stage: {ctx.get('lead', {}).get('stage', 'N/A')}
BRAND VOICE: {ctx.get('brand', {}).get('voice', '')}
CONVERSATION HISTORY: {ctx.get('conversation_history', '')}
KNOWLEDGE BASE: {ctx.get('knowledge_base', '')}

Respond with JSON: {{
  "reasoning": "...",
  "proposals": [
    {{
      "action_type": "...",
      "payload": {{...}},
      "rationale": "...",
      "evidence": {{...}},
      "risk_tier": 0-3
    }}
  ],
  "done": true/false
}}
"""
        
        # Call LLM
        try:
            result = complete_json(LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_content)
                ],
                tier=model_tier,
                temperature=0.2,
                org_id=ctx.get('org_id')
            ))
        except Exception as e:
            return {
                "done": True,
                "error": str(e),
                "iteration": state["iteration"] + 1
            }
        
        return {
            "proposals": state["proposals"] + result.get("proposals", []),
            "done": result.get("done", True),
            "iteration": state["iteration"] + 1,
        }
    
    return reason_node


def should_continue_node(state: AgentState) -> dict:
    """
    Conditional routing node.
    """
    return {}  # Routing is handled by the conditional edge


def run_agent_graph(compiled_graph, context_dict: dict) -> List[dict]:
    """
    Executes the agent graph and returns proposals.
    """
    initial_state = {
        "messages": [],
        "proposals": [],
        "context": context_dict,
        "iteration": 0,
        "done": False,
        "error": None
    }
    
    final_state = compiled_graph.invoke(initial_state)
    return final_state["proposals"]
