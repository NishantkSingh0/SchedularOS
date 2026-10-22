"""
Web Search Connector
Implements web search functionality using Bing Search API
"""
import os
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single web search result"""
    title: str
    url: str
    snippet: str
    source: str


class WebSearchConnector:
    """Connector for web search operations using Bing Search API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize web search connector
        
        Args:
            api_key: API key for Bing Search API (defaults to env var SEARCH_API_KEY)
        """
        self.api_key = api_key or os.getenv('SEARCH_API_KEY')
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform a web search
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            # Return mock results for demo purposes if no API key
            return self._get_mock_results(query, num_results)
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "responseFilter": "webpages"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:num_results]:
                    results.append(SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source="bing"
                    ))
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Web search failed: {str(e)}")
    
    def search_news(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform a news search
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            return self._get_mock_news_results(query, num_results)
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "responseFilter": "news"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "news" in data and "value" in data["news"]:
                for item in data["news"]["value"][:num_results]:
                    results.append(SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        source="bing_news"
                    ))
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"News search failed: {str(e)}")
    
    def _get_mock_results(self, query: str, num_results: int) -> List[SearchResult]:
        """Return mock results for demo purposes when no API key is configured"""
        return [
            SearchResult(
                title=f"Sample result for: {query}",
                url=f"https://example.com/{query.replace(' ', '-')}",
                snippet=f"This is a mock result for the query '{query}'. Configure SEARCH_API_KEY in .env to get real search results.",
                source="mock"
            )
        ] * min(num_results, 1)
    
    def _get_mock_news_results(self, query: str, num_results: int) -> List[SearchResult]:
        """Return mock news results for demo purposes when no API key is configured"""
        return [
            SearchResult(
                title=f"Sample news for: {query}",
                url=f"https://news.example.com/{query.replace(' ', '-')}",
                snippet=f"This is a mock news result for the query '{query}'. Configure SEARCH_API_KEY in .env to get real search results.",
                source="mock_news"
            )
        ] * min(num_results, 1)


# Singleton instance
_search_connector: Optional[WebSearchConnector] = None


def get_web_search_connector() -> WebSearchConnector:
    """Get or create the web search connector singleton"""
    global _search_connector
    if _search_connector is None:
        _search_connector = WebSearchConnector()
    return _search_connector
