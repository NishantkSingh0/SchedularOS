"""
Google Ads Connector
Implements Google Ads API integration for campaign management
"""
import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class GoogleCampaign:
    """Represents a Google Ads campaign"""
    id: str
    name: str
    status: str
    advertising_channel_type: str
    budget_amount_micros: float
    metrics_impressions: int
    metrics_clicks: int
    metrics_cost_micros: float
    metrics_conversions: int


@dataclass
class GoogleAdGroup:
    """Represents a Google Ads ad group"""
    id: str
    name: str
    status: str
    campaign_id: str
    cpc_bid_micros: float


class GoogleAdsConnector:
    """Connector for Google Ads API"""
    
    def __init__(self, developer_token: Optional[str] = None, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None, refresh_token: Optional[str] = None,
                 customer_id: Optional[str] = None):
        """
        Initialize Google Ads connector
        
        Args:
            developer_token: Google Ads developer token
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_token: OAuth2 refresh token
            customer_id: Google Ads customer ID
        """
        self.developer_token = developer_token or os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
        self.client_id = client_id or os.getenv('GOOGLE_ADS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('GOOGLE_ADS_CLIENT_SECRET')
        self.refresh_token = refresh_token or os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
        self.customer_id = customer_id or os.getenv('GOOGLE_ADS_CUSTOMER_ID')
        self.base_url = "https://googleads.googleapis.com/v16"
        
        self.access_token = None
        
        if not self.developer_token:
            raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN not configured")
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token using refresh token"""
        if not self.refresh_token:
            raise ValueError("GOOGLE_ADS_REFRESH_TOKEN not configured")
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            return self.access_token
        except requests.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to Google Ads API"""
        if not self.access_token:
            self._get_access_token()
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=data, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def get_campaigns(self) -> List[GoogleCampaign]:
        """
        Get all campaigns for the customer
        
        Returns:
            List of GoogleCampaign objects
        """
        if not self.customer_id:
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID not configured")
        
        query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        ORDER BY campaign.name
        """
        
        endpoint = f"customers/{self.customer_id}/googleAds:searchStream"
        data = {"query": query}
        
        try:
            response_data = self._make_request(endpoint, "POST", data)
            
            campaigns = []
            if "results" in response_data:
                for item in response_data["results"]:
                    campaign = item.get("campaign", {})
                    metrics = item.get("metrics", {})
                    
                    campaigns.append(GoogleCampaign(
                        id=campaign.get("id", ""),
                        name=campaign.get("name", ""),
                        status=campaign.get("status", ""),
                        advertising_channel_type=campaign.get("advertisingChannelType", ""),
                        budget_amount_micros=float(campaign.get("budget", {}).get("amountMicros", 0)),
                        metrics_impressions=int(metrics.get("impressions", 0)),
                        metrics_clicks=int(metrics.get("clicks", 0)),
                        metrics_cost_micros=float(metrics.get("costMicros", 0)),
                        metrics_conversions=int(metrics.get("conversions", 0))
                    ))
            
            return campaigns
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch campaigns: {str(e)}")
    
    def create_campaign(self, name: str, advertising_channel_type: str, budget_micros: float) -> GoogleCampaign:
        """
        Create a new campaign
        
        Args:
            name: Campaign name
            advertising_channel_type: Channel type (SEARCH, DISPLAY, VIDEO, etc.)
            budget_micros: Budget in micros
            
        Returns:
            Created GoogleCampaign object
        """
        if not self.customer_id:
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID not configured")
        
        # First create a budget
        budget_query = f"""
        INSERT INTO campaign_budget (campaign_budget.name, amount_micros)
        VALUES ('{name} Budget', {budget_micros})
        """
        
        budget_endpoint = f"customers/{self.customer_id}/campaignBudgets:mutate"
        budget_data = {
            "operations": [{
                "create": {
                    "campaignBudget": {
                        "name": f"{name} Budget",
                        "amountMicros": budget_micros
                    }
                }
            }]
        }
        
        try:
            budget_response = self._make_request(budget_endpoint, "POST", budget_data)
            budget_name = budget_response.get("results", [{}])[0].get("campaignBudget", {}).get("resourceName", "")
            
            # Then create the campaign
            campaign_query = f"""
            INSERT INTO campaign
            (name, advertising_channel_type, campaign_budget)
            VALUES ('{name}', '{advertising_channel_type}', '{budget_name}')
            """
            
            campaign_endpoint = f"customers/{self.customer_id}/campaigns:mutate"
            campaign_data = {
                "operations": [{
                    "create": {
                        "campaign": {
                            "name": name,
                            "advertisingChannelType": advertising_channel_type,
                            "campaignBudget": budget_name,
                            "status": "PAUSED"
                        }
                    }
                }]
            }
            
            campaign_response = self._make_request(campaign_endpoint, "POST", campaign_data)
            campaign = campaign_response.get("results", [{}])[0].get("campaign", {})
            
            return GoogleCampaign(
                id=campaign.get("id", ""),
                name=campaign.get("name", ""),
                status=campaign.get("status", ""),
                advertising_channel_type=campaign.get("advertisingChannelType", ""),
                budget_amount_micros=budget_micros,
                metrics_impressions=0,
                metrics_clicks=0,
                metrics_cost_micros=0,
                metrics_conversions=0
            )
            
        except requests.RequestException as e:
            raise Exception(f"Failed to create campaign: {str(e)}")
    
    def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        """
        Update campaign status
        
        Args:
            campaign_id: Campaign resource name
            status: New status (ENABLED, PAUSED, REMOVED)
            
        Returns:
            True if successful
        """
        if not self.customer_id:
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID not configured")
        
        endpoint = f"customers/{self.customer_id}/campaigns:mutate"
        
        data = {
            "operations": [{
                "update": {
                    "resourceName": campaign_id,
                    "campaign": {
                        "status": status
                    }
                }
            }]
        }
        
        try:
            self._make_request(endpoint, "POST", data)
            return True
        except requests.RequestException as e:
            raise Exception(f"Failed to update campaign status: {str(e)}")
    
    def get_ad_groups(self, campaign_id: str) -> List[GoogleAdGroup]:
        """
        Get ad groups for a campaign
        
        Args:
            campaign_id: Campaign resource name
            
        Returns:
            List of GoogleAdGroup objects
        """
        if not self.customer_id:
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID not configured")
        
        query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            ad_group.status,
            ad_group.campaign,
            ad_group.cpc_bid_micros
        FROM ad_group
        WHERE ad_group.campaign = '{campaign_id}'
        ORDER BY ad_group.name
        """
        
        endpoint = f"customers/{self.customer_id}/googleAds:searchStream"
        data = {"query": query}
        
        try:
            response_data = self._make_request(endpoint, "POST", data)
            
            ad_groups = []
            if "results" in response_data:
                for item in response_data["results"]:
                    ad_group = item.get("adGroup", {})
                    
                    ad_groups.append(GoogleAdGroup(
                        id=ad_group.get("id", ""),
                        name=ad_group.get("name", ""),
                        status=ad_group.get("status", ""),
                        campaign_id=ad_group.get("campaign", ""),
                        cpc_bid_micros=float(ad_group.get("cpcBidMicros", 0))
                    ))
            
            return ad_groups
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch ad groups: {str(e)}")


# Singleton instance
_google_ads_connector: Optional[GoogleAdsConnector] = None


def get_google_ads_connector() -> GoogleAdsConnector:
    """Get or create the Google Ads connector singleton"""
    global _google_ads_connector
    if _google_ads_connector is None:
        _google_ads_connector = GoogleAdsConnector()
    return _google_ads_connector
