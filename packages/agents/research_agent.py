"""
Research Agent
Performs market, customer, competitor, and audience research using web search and LLM analysis
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import sys
import os

# Add parent packages to path
current_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.dirname(current_dir)
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway
from connectors.web_search import WebSearchConnector, get_web_search_connector


@dataclass
class ResearchResult:
    """Represents research findings"""
    topic: str
    findings: str
    sources: List[str]
    confidence: float
    metadata: Dict[str, Any]


class ResearchAgent:
    """Agent for conducting marketing research"""
    
    def __init__(self, llm_gateway: Optional[LLMGateway] = None, search_connector: Optional[WebSearchConnector] = None):
        """
        Initialize research agent
        
        Args:
            llm_gateway: LLM gateway instance (optional, uses singleton if not provided)
            search_connector: Web search connector instance (optional, uses singleton if not provided)
        """
        self.llm_gateway = llm_gateway or get_llm_gateway()
        self.search_connector = search_connector or get_web_search_connector()
    
    def research_market(self, industry: str, company_context: Optional[str] = None) -> ResearchResult:
        """
        Research market trends and landscape
        
        Args:
            industry: Industry or market to research
            company_context: Optional context about the company for personalized research
            
        Returns:
            ResearchResult with market findings
        """
        # Search for market information
        queries = [
            f"{industry} market trends 2024",
            f"{industry} market size growth",
            f"{industry} industry analysis"
        ]
        
        all_results = []
        sources = []
        
        for query in queries:
            try:
                results = self.search_connector.search(query, num_results=5)
                all_results.extend(results)
                sources.extend([r.url for r in results])
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
        
        # Analyze findings with LLM
        if all_results:
            search_summary = "\n".join([f"- {r.title}: {r.snippet}" for r in all_results])
            
            system_prompt = "You are a market research analyst. Analyze the provided search results and synthesize key insights about market trends, size, and growth opportunities."
            
            user_prompt = f"""Research the {industry} market.

Company Context:
{company_context or "No specific company context provided"}

Search Results:
{search_summary}

Provide a comprehensive market analysis including:
1. Market size and growth rate
2. Key trends and drivers
3. Major players and competition
4. Opportunities and challenges
5. Recommendations for market entry or expansion"""
            
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]
            
            try:
                response = self.llm_gateway.generate(messages, temperature=0.7)
                return ResearchResult(
                    topic=f"Market Research: {industry}",
                    findings=response.content,
                    sources=list(set(sources)),
                    confidence=0.8,
                    metadata={"provider": response.provider, "num_sources": len(sources)}
                )
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                # Fallback to summary
                return ResearchResult(
                    topic=f"Market Research: {industry}",
                    findings=search_summary,
                    sources=list(set(sources)),
                    confidence=0.5,
                    metadata={"error": str(e)}
                )
        else:
            return ResearchResult(
                topic=f"Market Research: {industry}",
                findings="No search results found",
                sources=[],
                confidence=0.0,
                metadata={"error": "No results"}
            )
    
    def research_competitors(self, company_name: str, industry: str) -> ResearchResult:
        """
        Research competitors for a company
        
        Args:
            company_name: Name of the company
            industry: Industry of the company
            
        Returns:
            ResearchResult with competitor analysis
        """
        queries = [
            f"{company_name} competitors {industry}",
            f"top companies in {industry}",
            f"{industry} market leaders"
        ]
        
        all_results = []
        sources = []
        
        for query in queries:
            try:
                results = self.search_connector.search(query, num_results=5)
                all_results.extend(results)
                sources.extend([r.url for r in results])
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
        
        if all_results:
            search_summary = "\n".join([f"- {r.title}: {r.snippet}" for r in all_results])
            
            system_prompt = "You are a competitive intelligence analyst. Analyze the provided search results to identify key competitors, their strengths, weaknesses, and market positioning."
            
            user_prompt = f"""Analyze competitors for {company_name} in the {industry} industry.

Search Results:
{search_summary}

Provide a competitive analysis including:
1. Top 5-10 direct competitors
2. Their market share and positioning
3. Strengths and weaknesses of each
4. Differentiation opportunities for {company_name}
5. Strategic recommendations"""
            
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]
            
            try:
                response = self.llm_gateway.generate(messages, temperature=0.7)
                return ResearchResult(
                    topic=f"Competitor Analysis: {company_name}",
                    findings=response.content,
                    sources=list(set(sources)),
                    confidence=0.8,
                    metadata={"provider": response.provider, "num_sources": len(sources)}
                )
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return ResearchResult(
                    topic=f"Competitor Analysis: {company_name}",
                    findings=search_summary,
                    sources=list(set(sources)),
                    confidence=0.5,
                    metadata={"error": str(e)}
                )
        else:
            return ResearchResult(
                topic=f"Competitor Analysis: {company_name}",
                findings="No search results found",
                sources=[],
                confidence=0.0,
                metadata={"error": "No results"}
            )
    
    def research_audience(self, product: str, industry: str) -> ResearchResult:
        """
        Research target audience for a product
        
        Args:
            product: Product or service to research audience for
            industry: Industry of the product
            
        Returns:
            ResearchResult with audience analysis
        """
        queries = [
            f"target audience for {product}",
            f"{industry} customer demographics",
            f"who buys {product}"
        ]
        
        all_results = []
        sources = []
        
        for query in queries:
            try:
                results = self.search_connector.search(query, num_results=5)
                all_results.extend(results)
                sources.extend([r.url for r in results])
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
        
        if all_results:
            search_summary = "\n".join([f"- {r.title}: {r.snippet}" for r in all_results])
            
            system_prompt = "You are a market research analyst specializing in audience analysis. Analyze the provided search results to identify target audience demographics, psychographics, and behaviors."
            
            user_prompt = f"""Research the target audience for {product} in the {industry} industry.

Search Results:
{search_summary}

Provide an audience analysis including:
1. Demographics (age, gender, income, location)
2. Psychographics (interests, values, lifestyle)
3. Pain points and needs
4. Buying behavior and decision factors
5. Recommended marketing channels and messaging"""
            
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]
            
            try:
                response = self.llm_gateway.generate(messages, temperature=0.7)
                return ResearchResult(
                    topic=f"Audience Research: {product}",
                    findings=response.content,
                    sources=list(set(sources)),
                    confidence=0.8,
                    metadata={"provider": response.provider, "num_sources": len(sources)}
                )
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return ResearchResult(
                    topic=f"Audience Research: {product}",
                    findings=search_summary,
                    sources=list(set(sources)),
                    confidence=0.5,
                    metadata={"error": str(e)}
                )
        else:
            return ResearchResult(
                topic=f"Audience Research: {product}",
                findings="No search results found",
                sources=[],
                confidence=0.0,
                metadata={"error": "No results"}
            )


# Singleton instance
_research_agent: Optional[ResearchAgent] = None


def get_research_agent() -> ResearchAgent:
    """Get or create the research agent singleton"""
    global _research_agent
    if _research_agent is None:
        _research_agent = ResearchAgent()
    return _research_agent
