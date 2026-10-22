"""
LangGraph Orchestration
Defines agent graphs for coordinating multiple agents in workflows
"""
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
import sys
import os

# Add parent packages to path
current_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.dirname(current_dir)
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)


class AgentState(TypedDict):
    """State passed between agents in the graph"""
    goal: str
    context: Dict[str, Any]
    research_results: List[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    current_step: str
    errors: List[str]


class OrchestratorGraph:
    """Orchestrator agent graph for coordinating marketing workflows"""
    
    def __init__(self):
        """Initialize the orchestrator graph"""
        self.graph = StateGraph(AgentState)
        self._build_graph()
        self.memory = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)
    
    def _build_graph(self):
        """Build the agent graph with nodes and edges"""
        # Add nodes for each agent step
        self.graph.add_node("research", self._research_node)
        self.graph.add_node("analyze", self._analyze_node)
        self.graph.add_node("propose", self._propose_node)
        self.graph.add_node("decision", self._decision_node)
        
        # Define the flow
        self.graph.set_entry_point("research")
        self.graph.add_edge("research", "analyze")
        self.graph.add_edge("analyze", "propose")
        self.graph.add_edge("propose", "decision")
        self.graph.add_edge("decision", END)
    
    def _research_node(self, state: AgentState) -> AgentState:
        """Research node - gather information"""
        from agents.research_agent import ResearchAgent
        
        research_agent = ResearchAgent()
        
        # Perform research based on goal
        industry = state["context"].get("industry", "")
        company = state["context"].get("company_name", "")
        
        try:
            market_result = research_agent.research_market(industry)
            state["research_results"].append({
                "type": "market",
                "data": market_result.__dict__
            })
            
            if company:
                competitor_result = research_agent.research_competitors(company, industry)
                state["research_results"].append({
                    "type": "competitors",
                    "data": competitor_result.__dict__
                })
            
            state["current_step"] = "research_completed"
        except Exception as e:
            state["errors"].append(f"Research failed: {str(e)}")
        
        return state
    
    def _analyze_node(self, state: AgentState) -> AgentState:
        """Analysis node - analyze research findings"""
        from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway
        
        llm_gateway = get_llm_gateway()
        
        # Compile research findings
        findings_summary = "\n".join([
            f"{r['type']}: {r['data'].get('findings', '')[:200]}..."
            for r in state["research_results"]
        ])
        
        system_prompt = "You are a marketing strategist. Analyze research findings and extract key insights."
        user_prompt = f"""Analyze these research findings for the goal: {state['goal']}

Research Findings:
{findings_summary}

Provide:
1. Key insights
2. Opportunities
3. Risks
4. Recommendations"""
        
        try:
            response = llm_gateway.generate([
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ])
            
            state["context"]["analysis"] = response.content
            state["current_step"] = "analysis_completed"
        except Exception as e:
            state["errors"].append(f"Analysis failed: {str(e)}")
        
        return state
    
    def _propose_node(self, state: AgentState) -> AgentState:
        """Proposal node - generate action proposals"""
        from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway
        
        llm_gateway = get_llm_gateway()
        
        system_prompt = "You are a marketing automation specialist. Generate actionable proposals based on analysis."
        user_prompt = f"""Generate marketing proposals for: {state['goal']}

Analysis:
{state['context'].get('analysis', 'No analysis available')}

Generate 3-5 specific proposals with:
1. Title
2. Description
3. Expected impact
4. Estimated effort
5. Risk level"""
        
        try:
            response = llm_gateway.generate([
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ])
            
            state["proposals"].append({
                "content": response.content,
                "source": "orchestrator"
            })
            state["current_step"] = "proposals_generated"
        except Exception as e:
            state["errors"].append(f"Proposal generation failed: {str(e)}")
        
        return state
    
    def _decision_node(self, state: AgentState) -> AgentState:
        """Decision node - evaluate proposals and recommend action"""
        state["current_step"] = "decision_made"
        return state
    
    def run(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the orchestrator graph
        
        Args:
            goal: The marketing goal to achieve
            context: Additional context (industry, company, etc.)
            
        Returns:
            Final state with results
        """
        initial_state = AgentState(
            goal=goal,
            context=context,
            research_results=[],
            proposals=[],
            current_step="initialized",
            errors=[]
        )
        
        # Run the graph
        config = {"configurable": {"thread_id": "marketing-orchestrator"}}
        final_state = self.compiled_graph.invoke(initial_state, config)
        
        return final_state


class MarketingWorkflowGraph:
    """Specific workflow for marketing automation tasks"""
    
    def __init__(self):
        """Initialize the marketing workflow graph"""
        self.graph = StateGraph(AgentState)
        self._build_graph()
        self.memory = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)
    
    def _build_graph(self):
        """Build the marketing workflow graph"""
        self.graph.add_node("market_research", self._market_research_node)
        self.graph.add_node("audience_research", self._audience_research_node)
        self.graph.add_node("content_strategy", self._content_strategy_node)
        self.graph.add_node("campaign_proposal", self._campaign_proposal_node)
        
        self.graph.set_entry_point("market_research")
        self.graph.add_edge("market_research", "audience_research")
        self.graph.add_edge("audience_research", "content_strategy")
        self.graph.add_edge("content_strategy", "campaign_proposal")
        self.graph.add_edge("campaign_proposal", END)
    
    def _market_research_node(self, state: AgentState) -> AgentState:
        """Market research step"""
        from agents.research_agent import ResearchAgent
        
        research_agent = ResearchAgent()
        industry = state["context"].get("industry", "")
        
        try:
            result = research_agent.research_market(industry)
            state["research_results"].append({
                "type": "market",
                "data": result.__dict__
            })
            state["current_step"] = "market_research_completed"
        except Exception as e:
            state["errors"].append(f"Market research failed: {str(e)}")
        
        return state
    
    def _audience_research_node(self, state: AgentState) -> AgentState:
        """Audience research step"""
        from agents.research_agent import ResearchAgent
        
        research_agent = ResearchAgent()
        product = state["context"].get("product", "")
        industry = state["context"].get("industry", "")
        
        try:
            result = research_agent.research_audience(product, industry)
            state["research_results"].append({
                "type": "audience",
                "data": result.__dict__
            })
            state["current_step"] = "audience_research_completed"
        except Exception as e:
            state["errors"].append(f"Audience research failed: {str(e)}")
        
        return state
    
    def _content_strategy_node(self, state: AgentState) -> AgentState:
        """Content strategy generation step"""
        from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway
        
        llm_gateway = get_llm_gateway()
        
        findings_summary = "\n".join([
            f"{r['type']}: {r['data'].get('findings', '')[:200]}..."
            for r in state["research_results"]
        ])
        
        system_prompt = "You are a content strategist. Develop a content strategy based on research."
        user_prompt = f"""Create a content strategy for: {state['goal']}

Research Findings:
{findings_summary}

Provide:
1. Content themes
2. Channel recommendations
3. Content calendar outline
4. KPIs to track"""
        
        try:
            response = llm_gateway.generate([
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ])
            
            state["context"]["content_strategy"] = response.content
            state["current_step"] = "content_strategy_completed"
        except Exception as e:
            state["errors"].append(f"Content strategy failed: {str(e)}")
        
        return state
    
    def _campaign_proposal_node(self, state: AgentState) -> AgentState:
        """Campaign proposal generation step"""
        from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway
        
        llm_gateway = get_llm_gateway()
        
        system_prompt = "You are a campaign planner. Create a detailed campaign proposal."
        user_prompt = f"""Create a marketing campaign proposal for: {state['goal']}

Content Strategy:
{state['context'].get('content_strategy', 'No strategy available')}

Provide a complete campaign proposal with:
1. Campaign objectives
2. Target audience
3. Creative concepts
4. Channel mix
5. Budget allocation
6. Timeline
7. Success metrics"""
        
        try:
            response = llm_gateway.generate([
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ])
            
            state["proposals"].append({
                "content": response.content,
                "source": "marketing_workflow"
            })
            state["current_step"] = "campaign_proposal_completed"
        except Exception as e:
            state["errors"].append(f"Campaign proposal failed: {str(e)}")
        
        return state
    
    def run(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the marketing workflow graph
        
        Args:
            goal: The marketing goal
            context: Additional context
            
        Returns:
            Final state with results
        """
        initial_state = AgentState(
            goal=goal,
            context=context,
            research_results=[],
            proposals=[],
            current_step="initialized",
            errors=[]
        )
        
        config = {"configurable": {"thread_id": "marketing-workflow"}}
        final_state = self.compiled_graph.invoke(initial_state, config)
        
        return final_state
