"""
Meta MCP Server
Implements actual Meta Marketing API integration for campaign management
"""
import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Campaign:
    """Represents a Meta ad campaign"""
    id: str
    name: str
    status: str
    objective: str
    budget: float
    spend: float
    impressions: int
    clicks: int
    conversions: int


@dataclass
class AdCreative:
    """Represents an ad creative"""
    id: str
    name: str
    status: str
    preview_url: str
    thumbnail_url: str


class MetaConnector:
    """Connector for Meta Marketing API (Facebook/Instagram Ads)"""
    
    def __init__(self, access_token: Optional[str] = None, ad_account_id: Optional[str] = None):
        """
        Initialize Meta connector
        
        Args:
            access_token: Meta API access token
            ad_account_id: Meta Ad Account ID
        """
        self.access_token = access_token or os.getenv('META_ACCESS_TOKEN')
        self.ad_account_id = ad_account_id or os.getenv('META_AD_ACCOUNT_ID')
        self.base_url = "https://graph.facebook.com/v19.0"
        
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN not configured")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to Meta API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=data, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def get_campaigns(self) -> List[Campaign]:
        """
        Get all campaigns for the ad account
        
        Returns:
            List of Campaign objects
        """
        if not self.ad_account_id:
            raise ValueError("META_AD_ACCOUNT_ID not configured")
        
        endpoint = f"act_{self.ad_account_id}/campaigns"
        params = {
            "fields": "id,name,status,objective,budget_usage,spend,impressions,clicks,conversions"
        }
        
        try:
            data = self._make_request(endpoint, "GET", params)
            
            campaigns = []
            if "data" in data:
                for item in data["data"]:
                    campaigns.append(Campaign(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        status=item.get("status", ""),
                        objective=item.get("objective", ""),
                        budget=float(item.get("budget_usage", {}).get("budget", 0)),
                        spend=float(item.get("spend", 0)),
                        impressions=int(item.get("impressions", 0)),
                        clicks=int(item.get("clicks", 0)),
                        conversions=int(item.get("conversions", 0))
                    ))
            
            return campaigns
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch campaigns: {str(e)}")
    
    def create_campaign(self, name: str, objective: str, budget: float, daily_budget: Optional[float] = None) -> Campaign:
        """
        Create a new campaign
        
        Args:
            name: Campaign name
            objective: Campaign objective (e.g., OUTCOME_TRAFFIC, BRAND_AWARENESS)
            budget: Total budget
            daily_budget: Optional daily budget limit
            
        Returns:
            Created Campaign object
        """
        if not self.ad_account_id:
            raise ValueError("META_AD_ACCOUNT_ID not configured")
        
        endpoint = f"act_{self.ad_account_id}/campaigns"
        
        data = {
            "name": name,
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": []
        }
        
        if daily_budget:
            data["daily_budget"] = daily_budget
        
        try:
            response = self._make_request(endpoint, "POST", data)
            
            return Campaign(
                id=response.get("id", ""),
                name=response.get("name", ""),
                status=response.get("status", ""),
                objective=response.get("objective", ""),
                budget=float(response.get("budget_usage", {}).get("budget", 0)),
                spend=0.0,
                impressions=0,
                clicks=0,
                conversions=0
            )
            
        except requests.RequestException as e:
            raise Exception(f"Failed to create campaign: {str(e)}")
    
    def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        """
        Update campaign status
        
        Args:
            campaign_id: Campaign ID
            status: New status (ACTIVE, PAUSED, ARCHIVED)
            
        Returns:
            True if successful
        """
        endpoint = f"{campaign_id}"
        
        data = {"status": status}
        
        try:
            self._make_request(endpoint, "POST", data)
            return True
        except requests.RequestException as e:
            raise Exception(f"Failed to update campaign status: {str(e)}")
    
    def get_ad_creatives(self, campaign_id: str) -> List[AdCreative]:
        """
        Get ad creatives for a campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of AdCreative objects
        """
        endpoint = f"{campaign_id}/adcreatives"
        params = {
            "fields": "id,name,status,preview_url,thumbnail_url"
        }
        
        try:
            data = self._make_request(endpoint, "GET", params)
            
            creatives = []
            if "data" in data:
                for item in data["data"]:
                    creatives.append(AdCreative(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        status=item.get("status", ""),
                        preview_url=item.get("preview_url", ""),
                        thumbnail_url=item.get("thumbnail_url", "")
                    ))
            
            return creatives
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch ad creatives: {str(e)}")
    
    def get_campaign_insights(self, campaign_id: str, date_preset: str = "last_30d") -> Dict[str, Any]:
        """
        Get campaign insights
        
        Args:
            campaign_id: Campaign ID
            date_preset: Date range (last_7d, last_30d, last_90d, this_month, last_month, this_year)
            
        Returns:
            Dictionary with insights data
        """
        endpoint = f"{campaign_id}/insights"
        params = {
            "date_preset": date_preset,
            "fields": "impressions,clicks,spend,cpc,ctr,conversions,cost_per_conversion"
        }
        
        try:
            data = self._make_request(endpoint, "GET", params)
            
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]
            
            return {}
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch campaign insights: {str(e)}")


# Singleton instance
_meta_connector: Optional[MetaConnector] = None


def get_meta_connector() -> MetaConnector:
    """Get or create the Meta connector singleton"""
    global _meta_connector
    if _meta_connector is None:
        _meta_connector = MetaConnector()
    return _meta_connector
