import hashlib
import json
import time
import httpx
from typing import Optional
from llm_gateway.types import LLMRequest, LLMResponse, LLMMessage, ModelTier


class LLMGateway:
    """
    LLM Gateway that routes requests to Jev or OpenAI based on configuration.
    Implements caching, retry logic, and usage tracking.
    """
    
    def __init__(self, config: dict, redis_client=None):
        self.config = config
        self.redis = redis_client
        self.use_jev = bool(config.get('jev_api_key'))
        
        # OpenAI client (fallback)
        if config.get('fallback_to_openai') and config.get('openai_api_key'):
            import openai
            self.openai_client = openai.OpenAI(api_key=config['openai_api_key'])
        else:
            self.openai_client = None
    
    def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Complete a text generation request.
        All LLM calls go through this function.
        """
        # 1. Build cache key
        cache_key = self._build_cache_key(request)
        
        # 2. Check Redis cache
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                cached_data = json.loads(cached)
                return LLMResponse(
                    content=cached_data['content'],
                    model=cached_data['model'],
                    prompt_tokens=cached_data['prompt_tokens'],
                    completion_tokens=cached_data['completion_tokens'],
                    latency_ms=cached_data['latency_ms'],
                    cached=True
                )
        
        # 3. Call appropriate LLM
        if self.use_jev:
            response = self._call_jev(request)
        elif self.openai_client:
            response = self._call_openai(request)
        else:
            response = self._mock_response(request)
        
        # 4. Cache result
        if self.redis:
            ttl = self._get_cache_ttl(request.tier)
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps({
                    'content': response.content,
                    'model': response.model,
                    'prompt_tokens': response.prompt_tokens,
                    'completion_tokens': response.completion_tokens,
                    'latency_ms': response.latency_ms
                })
            )
        
        return response
    
    def complete_json(self, request: LLMRequest) -> dict:
        """
        Forces JSON response for structured agentic decisions.
        """
        # Append JSON constraint to last message
        request.messages[-1].content += "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        
        response = self.complete(request)
        
        # Strip markdown code fences if present
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract JSON with regex
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {"error": "json_parse_failed", "raw": content}
    
    def embed_text(self, text: str) -> list:
        """
        Generate embedding for text.
        """
        if self.openai_client:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        else:
            # Placeholder for Jev embedding
            raise NotImplementedError("Embeddings not yet implemented for Jev")
    
    def _mock_response(self, request: LLMRequest) -> LLMResponse:
        """
        Deterministic mock response when no LLM provider is configured.
        Content is valid JSON so complete_json() and agent graphs keep working.
        """
        content = json.dumps({
            "reasoning": "Mock response - no LLM provider configured (set JEV_API_KEY or OPENAI_API_KEY).",
            "proposals": [],
            "steps": [],
            "done": True,
        })
        return LLMResponse(
            content=content,
            model="mock",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=0
        )

    def _build_cache_key(self, request: LLMRequest) -> str:
        """Build cache key from request"""
        org_id = request.org_id or "default"
        messages_str = json.dumps([m.__dict__ for m in request.messages])
        key_str = f"{org_id}:{messages_str}:{request.tier.value}:{request.temperature}"
        return f"sos:{org_id}:cache:llm:{hashlib.sha256(key_str.encode()).hexdigest()}"
    
    def _get_cache_ttl(self, tier: ModelTier) -> int:
        """Get cache TTL for model tier"""
        return {
            ModelTier.FAST: self.config.get('cache_ttl_fast', 300),
            ModelTier.BALANCED: self.config.get('cache_ttl_balanced', 600),
            ModelTier.DEEP: self.config.get('cache_ttl_deep', 1800),
            ModelTier.DECISION: 600,
        }[tier]
    
    def _call_jev(self, request: LLMRequest) -> LLMResponse:
        """Call Jev API"""
        model_name = self._get_model_name(request.tier)
        
        start_time = time.time()
        
        try:
            response = httpx.post(
                f"{self.config['jev_api_endpoint']}/chat/completions",
                headers={"Authorization": f"Bearer {self.config['jev_api_key']}"},
                json={
                    "model": model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
                timeout=30
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            # Fallback to OpenAI if Jev fails
            if self.openai_client:
                return self._call_openai(request)
            raise RuntimeError(f"Jev API error: {e}")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Extract response
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model=model_name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms
        )
    
    def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API as fallback"""
        model_name = self._get_openai_model_name(request.tier)
        
        start_time = time.time()
        
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=model_name,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=latency_ms
        )
    
    def _get_model_name(self, tier: ModelTier) -> str:
        """Get Jev model name for tier"""
        return {
            ModelTier.FAST: self.config.get('fast_model', 'jev-1.5-flash'),
            ModelTier.BALANCED: self.config.get('balanced_model', 'jev-1.5-pro'),
            ModelTier.DEEP: self.config.get('deep_model', 'jev-1.5-pro-deep'),
            ModelTier.DECISION: self.config.get('decision_model', 'jev-decision-v1'),
        }[tier]
    
    def _get_openai_model_name(self, tier: ModelTier) -> str:
        """Get OpenAI model name for tier"""
        return {
            ModelTier.FAST: self.config.get('openai_fast_model', 'gpt-4o-mini'),
            ModelTier.BALANCED: self.config.get('openai_balanced_model', 'gpt-4o'),
            ModelTier.DEEP: self.config.get('openai_deep_model', 'gpt-4o'),
            ModelTier.DECISION: self.config.get('openai_balanced_model', 'gpt-4o'),
        }[tier]


# Global instance (will be initialized by Django app)
_llm_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """Get global LLM gateway instance"""
    global _llm_gateway
    if _llm_gateway is None:
        from django.conf import settings
        import redis
        redis_client = redis.from_url(settings.REDIS_URL)
        _llm_gateway = LLMGateway(settings.LLM_CONFIG, redis_client)
    return _llm_gateway


def complete(request: LLMRequest) -> LLMResponse:
    """Convenience function to complete a request"""
    return get_llm_gateway().complete(request)


def complete_json(request: LLMRequest) -> dict:
    """Convenience function to complete a JSON request"""
    return get_llm_gateway().complete_json(request)


def embed_text(text: str) -> list:
    """Convenience function to generate embeddings"""
    return get_llm_gateway().embed_text(text)
