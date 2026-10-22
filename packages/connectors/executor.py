from typing import Dict, Any
from connectors.mcp_wrapper import get_mcp_client, run_async


class Executor:
    """
    THE ONLY component that touches the outside world.
    Routes proposals to appropriate MCP connectors.
    """
    
    def __init__(self):
        self._connectors = {
            "whatsapp": WhatsAppConnector(),
            "email": EmailConnector(),
            "meta": MetaConnector(),
            "google": GoogleConnector(),
            "content": ContentConnector(),
            "websearch": WebSearchConnector(),
        }
    
    def execute(self, proposal) -> Dict[str, Any]:
        """
        Execute a proposal by routing to the appropriate connector.
        """
        prefix = proposal.action_type.split(".")[0]
        
        # Internal actions (no external API call)
        if prefix in ["lead", "research", "followup", "lead_generation",
                      "conversion", "customer", "partnerships", "creative"]:
            return self._handle_internal(proposal)
        
        # External actions via MCP
        connector = self._connectors.get(prefix)
        if connector is None:
            raise ValueError(f"Unknown connector for action_type: {proposal.action_type}")
        
        # Execute via MCP
        result = connector.execute(proposal.action_type, proposal.payload)
        
        if not result.get("success", False):
            raise RuntimeError(f"Connector execution failed: {result.get('error')}")
        
        # Post-execution side effects
        self._record_outbound_message(proposal, result)
        self._update_lead_contact(proposal)
        
        return result
    
    def _handle_internal(self, proposal) -> Dict[str, Any]:
        """Handle internal actions without external API calls"""
        action_type = proposal.action_type
        lead = proposal.step.run.lead

        if action_type.startswith("lead.") and lead is None:
            raise ValueError(f"Action {action_type} requires a lead but the run has none")

        if action_type == "lead.tag":
            lead.tags = list(set(lead.tags + proposal.payload.get("tags", [])))
            lead.save()

        elif action_type == "lead.score":
            lead.score = proposal.payload.get("score", 0)
            lead.save()

        elif action_type == "lead.stage_update":
            lead.stage = proposal.payload.get("stage", lead.stage)
            lead.save()

        elif action_type == "research.analyse":
            # Write result to proposal output - no external call
            pass

        return {"success": True, "internal": True}
    
    def _record_outbound_message(self, proposal, result):
        """Record outbound message in Conversation and Message models"""
        # Implementation depends on the specific action type
        pass
    
    def _update_lead_contact(self, proposal):
        """Update Lead.last_contacted_at"""
        from django.utils import timezone

        lead = proposal.step.run.lead
        if lead:
            lead.last_contacted_at = timezone.now()
            lead.save()


class BaseConnector:
    """Base class for MCP-based connectors"""
    
    def __init__(self):
        self.config = {}
    
    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action via MCP"""
        raise NotImplementedError


class MetaConnector(BaseConnector):
    """Meta Ads/Graph connector — real Graph API calls when configured, MCP mock otherwise"""

    API_VERSION = "v19.0"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings

        access_token = settings.META_CONFIG.get('access_token')
        ad_account_id = settings.META_CONFIG.get('ad_account_id')

        if access_token and ad_account_id:
            return self._execute_real(action_type, payload, access_token, ad_account_id)
        return self._execute_mock(action_type, payload)

    def _execute_real(self, action_type, payload, access_token, ad_account_id):
        import httpx

        base = f"https://graph.facebook.com/{self.API_VERSION}"
        params = {"access_token": access_token}

        if action_type == "meta.create_campaign":
            resp = httpx.post(
                f"{base}/act_{ad_account_id}/campaigns",
                params=params,
                data={
                    "name": payload.get("name"),
                    "objective": payload.get("objective", "OUTCOME_LEADS"),
                    "status": payload.get("status", "PAUSED"),
                    "special_ad_categories": payload.get("special_ad_categories", "[]"),
                    "daily_budget": payload.get("daily_budget"),
                },
                timeout=30,
            )
        elif action_type == "meta.upload_content":
            resp = httpx.post(
                f"{base}/act_{ad_account_id}/adimages",
                params=params,
                data={"filename": payload.get("filename"), "bytes": payload.get("bytes")},
                timeout=60,
            )
        elif action_type == "meta.get_performance":
            resp = httpx.get(
                f"{base}/act_{ad_account_id}/insights",
                params={**params, "level": "campaign",
                        "date_preset": payload.get("date_preset", "last_30d")},
                timeout=30,
            )
        elif action_type == "meta.update_budget":
            resp = httpx.post(
                f"{base}/{payload.get('campaign_id')}",
                params=params,
                data={"daily_budget": payload.get("daily_budget")},
                timeout=30,
            )
        else:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return {"success": False, "error": data}
        external_id = data.get("id") or (data.get("data") or [{}])[0].get("campaign_id")
        return {"success": True, "external_id": external_id, "data": data}

    def _execute_mock(self, action_type, payload):
        client = get_mcp_client("meta", {})

        tool_map = {
            "meta.create_campaign": "create_campaign",
            "meta.upload_content": "upload_content",
            "meta.get_performance": "get_performance",
            "meta.update_budget": "update_budget",
        }
        tool = tool_map.get(action_type)
        if not tool:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        result = run_async(client.call_tool(tool, payload))
        return {"success": True, "external_id": result.get("id"), "data": result}


class GoogleConnector(BaseConnector):
    """Google Ads connector — real googleads REST API when configured, MCP mock otherwise"""

    API_VERSION = "v17"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings

        cfg = settings.GOOGLE_ADS_CONFIG
        configured = all([
            cfg.get('developer_token'), cfg.get('client_id'),
            cfg.get('client_secret'), cfg.get('refresh_token'),
            cfg.get('customer_id'),
        ])

        if configured:
            try:
                return self._execute_real(action_type, payload, cfg)
            except Exception as e:
                return {"success": False, "error": str(e)}
        return self._execute_mock(action_type, payload)

    def _access_token(self, cfg):
        import httpx

        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": cfg['client_id'],
                "client_secret": cfg['client_secret'],
                "refresh_token": cfg['refresh_token'],
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _execute_real(self, action_type, payload, cfg):
        import httpx

        token = self._access_token(cfg)
        customer_id = cfg['customer_id'].replace('-', '')
        base = f"https://googleads.googleapis.com/{self.API_VERSION}/customers/{customer_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "developer-token": cfg['developer_token'],
        }

        if action_type == "google.create_campaign":
            body = {"mutateOperations": [{"campaignOperation": {"create": {
                "name": payload.get("name"),
                "status": payload.get("status", "PAUSED"),
                "advertisingChannelType": payload.get("channel", "SEARCH"),
                "campaignBudget": payload.get("budget_resource"),
            }}}]}
            resp = httpx.post(f"{base}/googleAds:mutate", headers=headers,
                              json=body, timeout=30)
        elif action_type == "google.get_stats":
            query = payload.get("query") or (
                "SELECT campaign.id, campaign.name, metrics.impressions, "
                "metrics.clicks, metrics.cost_micros FROM campaign "
                "WHERE segments.date DURING LAST_30_DAYS"
            )
            resp = httpx.post(f"{base}/googleAds:search", headers=headers,
                              json={"query": query}, timeout=30)
        elif action_type == "google.pause_campaign":
            body = {"mutateOperations": [{"campaignOperation": {
                "update": {"resourceName": payload.get("campaign_resource"),
                           "status": "PAUSED"},
                "updateMask": "status",
            }}]}
            resp = httpx.post(f"{base}/googleAds:mutate", headers=headers,
                              json=body, timeout=30)
        else:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return {"success": False, "error": data}
        return {"success": True, "external_id": data.get("campaign_id"), "data": data}

    def _execute_mock(self, action_type, payload):
        client = get_mcp_client("google", {})

        tool_map = {
            "google.create_campaign": "create_google_campaign",
            "google.get_stats": "get_campaign_stats",
            "google.pause_campaign": "pause_campaign",
        }
        tool = tool_map.get(action_type)
        if not tool:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        result = run_async(client.call_tool(tool, payload))
        return {"success": True, "external_id": result.get("campaign_id"), "data": result}


class ContentConnector(BaseConnector):
    """Content generation connector — real image API when configured, MCP mock otherwise"""

    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings

        api_key = settings.CONTENT_GEN_CONFIG.get('api_key')
        if api_key:
            try:
                return self._execute_real(action_type, payload)
            except Exception as e:
                return {"success": False, "error": str(e)}
        return self._execute_mock(action_type, payload)

    def _execute_real(self, action_type, payload):
        import httpx
        from django.conf import settings

        cfg = settings.CONTENT_GEN_CONFIG
        endpoint = cfg.get('api_endpoint', 'https://api.openai.com/v1').rstrip('/')
        headers = {"Authorization": f"Bearer {cfg['api_key']}"}

        if action_type == "content.generate_image":
            resp = httpx.post(
                f"{endpoint}/images/generations",
                headers=headers,
                json={
                    "model": cfg.get('image_model', 'dall-e-3'),
                    "prompt": payload.get("prompt"),
                    "n": payload.get("n", 1),
                    "size": payload.get("size", "1024x1024"),
                },
                timeout=120,
            )
        elif action_type == "content.generate_video":
            return {"success": False, "error": "Video generation is not supported by the configured provider"}
        elif action_type == "content.enhance_prompt":
            resp = httpx.post(
                f"{endpoint}/chat/completions",
                headers=headers,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Enhance the following creative brief into a detailed image-generation prompt."},
                        {"role": "user", "content": payload.get("prompt", "")},
                    ],
                },
                timeout=60,
            )
        else:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return {"success": False, "error": data}
        return {"success": True, "data": data}

    def _execute_mock(self, action_type, payload):
        client = get_mcp_client("content", {})

        tool_map = {
            "content.generate_image": "generate_image",
            "content.generate_video": "generate_video",
            "content.enhance_prompt": "enhance_prompt",
        }
        tool = tool_map.get(action_type)
        if not tool:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        result = run_async(client.call_tool(tool, payload))
        return {"success": True, "data": result}


class WebSearchConnector(BaseConnector):
    """Web search connector — real Bing Search API when configured, MCP mock otherwise"""

    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings

        if settings.SEARCH_CONFIG.get('api_key'):
            return self._execute_real(action_type, payload)
        return self._execute_mock(action_type, payload)

    def _execute_real(self, action_type, payload):
        from connectors.web_search import WebSearchConnector as BingSearch

        search = BingSearch()
        if action_type == "web.search":
            results = search.search(payload.get("query", ""),
                                    num_results=payload.get("num_results", 10))
        elif action_type == "web.search_news":
            results = search.search_news(payload.get("query", ""),
                                         num_results=payload.get("num_results", 10))
        else:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        return {"success": True, "data": [r.__dict__ for r in results]}

    def _execute_mock(self, action_type, payload):
        client = get_mcp_client("websearch", {})

        tool_map = {
            "web.search": "web_search",
            "web.search_news": "search_news",
        }
        tool = tool_map.get(action_type)
        if not tool:
            return {"success": False, "error": f"Unknown action: {action_type}"}

        result = run_async(client.call_tool(tool, payload))
        return {"success": True, "data": result}


class WhatsAppConnector(BaseConnector):
    """WhatsApp connector via MCP"""
    
    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings
        import httpx
        
        if action_type == "whatsapp.send_message":
            phone_number_id = settings.META_CONFIG.get('phone_number_id')
            access_token = settings.META_CONFIG.get('access_token')

            if not access_token or not phone_number_id:
                return {"success": False, "error": "META credentials not configured"}

            response = httpx.post(
                f"https://graph.facebook.com/v19.0/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": payload.get("to"),
                    "type": "text",
                    "text": {"body": payload.get("body"), "preview_url": False}
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "external_id": data["messages"][0]["id"],
                    "data": data
                }
            else:
                return {"success": False, "error": response.text}
        
        return {"success": False, "error": f"Unknown action: {action_type}"}


class EmailConnector(BaseConnector):
    """Email connector — AWS SES when configured, mock otherwise"""

    def execute(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from django.conf import settings

        cfg = settings.EMAIL_CONFIG
        configured = all([
            cfg.get('aws_access_key_id'), cfg.get('aws_secret_access_key'),
            cfg.get('aws_ses_region'), cfg.get('verified_sender'),
        ])

        if action_type != "email.send":
            return {"success": False, "error": f"Unknown action: {action_type}"}

        if not configured:
            return {
                "success": True,
                "external_id": f"email-{hash(str(payload))}",
                "data": {"message": "Email sent (mock)"}
            }

        import boto3
        client = boto3.client(
            'ses',
            region_name=cfg['aws_ses_region'],
            aws_access_key_id=cfg['aws_access_key_id'],
            aws_secret_access_key=cfg['aws_secret_access_key'],
        )
        resp = client.send_email(
            Source=cfg['verified_sender'],
            Destination={'ToAddresses': payload.get('to', [])},
            Message={
                'Subject': {'Data': payload.get('subject', '')},
                'Body': {
                    'Text': {'Data': payload.get('body', '')},
                    **({'Html': {'Data': payload['html']}} if payload.get('html') else {}),
                },
            },
        )
        return {"success": True, "external_id": resp.get('MessageId'), "data": resp}
