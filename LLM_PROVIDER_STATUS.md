# LLM Provider Configuration — SchedularOS

## What Changed

### 1. JWT Secret Key Fix
- **Before**: JWT used `SECRET_KEY` for signing (ignored `JWT_SECRET_KEY`)
- **After**: JWT now uses `JWT_SECRET_KEY` from `.env` (falls back to `SECRET_KEY` if not set)
- **Location**: `apps/api/schedularos/settings.py` lines 212-222

### 2. Gemini & Anthropic Integration
- **Before**: `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` were in `.env.example` but never read
- **After**: Both are now configured in `settings.py` and wired into the LLM gateway
- **Location**: `apps/api/schedularos/settings.py` lines 238-274

### 3. LLM Gateway Multi-Provider Support
- **Before**: Only Jev and OpenAI were supported
- **After**: Now supports 4 providers with fallback chain:
  1. Jev (primary)
  2. OpenAI (fallback)
  3. Gemini (fallback)
  4. Anthropic (fallback)
  5. Mock (no keys configured)
- **Location**: `packages/llm_gateway/client.py`

### 4. Requirements Update
- Added `anthropic==0.44.0` to `requirements.txt`

---

## LLM Provider Priority Chain

The LLM gateway (`packages/llm_gateway/client.py`) tries providers in this order:

```
1. Jev API (if JEV_API_KEY is set)
2. OpenAI (if OPENAI_API_KEY is set)
3. Gemini (if GEMINI_API_KEY is set)
4. Anthropic (if ANTHROPIC_API_KEY is set)
5. Mock mode (deterministic JSON response, no external calls)
```

**If a provider fails**, it automatically falls back to the next available provider.

---

## Environment Variables (Now All Connected)

| Variable | Connected To | Fallback Model(s) |
|----------|--------------|-------------------|
| `JEV_API_KEY` | Jev LLM gateway | `jev-1.5-flash`, `jev-1.5-pro`, `jev-1.5-pro-deep`, `jev-decision-v1` |
| `OPENAI_API_KEY` | OpenAI (fallback) | `gpt-4o-mini`, `gpt-4o` |
| `GEMINI_API_KEY` | Gemini (fallback) | `gemini-1.5-flash`, `gemini-1.5-pro` |
| `ANTHROPIC_API_KEY` | Anthropic Claude (fallback) | `claude-3-5-haiku-20241022`, `claude-3-5-sonnet-20241022` |
| `JWT_SECRET_KEY` | JWT signing | Falls back to `SECRET_KEY` |

---

## Model Tier Mapping

Each provider maps to 4 tiers used by agents:

| Tier | Jev | OpenAI | Gemini | Anthropic |
|------|-----|--------|--------|-----------|
| **FAST** | `jev-1.5-flash` | `gpt-4o-mini` | `gemini-1.5-flash` | `claude-3-5-haiku-20241022` |
| **BALANCED** | `jev-1.5-pro` | `gpt-4o` | `gemini-1.5-pro` | `claude-3-5-sonnet-20241022` |
| **DEEP** | `jev-1.5-pro-deep` | `gpt-4o` | `gemini-1.5-pro` | `claude-3-5-sonnet-20241022` |
| **DECISION** | `jev-decision-v1` | `gpt-4o` | `gemini-1.5-pro` | `claude-3-5-sonnet-20241022` |

You can override these model names in `.env`:
- `JEV_FAST_MODEL`, `JEV_BALANCED_MODEL`, etc.
- `OPENAI_FAST_MODEL`, `OPENAI_BALANCED_MODEL`, etc.
- `GEMINI_FAST_MODEL`, `GEMINI_BALANCED_MODEL`, etc.
- `ANTHROPIC_FAST_MODEL`, `ANTHROPIC_BALANCED_MODEL`, etc.

---

## Embedding Support

Embeddings for RAG are supported from:
1. **OpenAI** (`text-embedding-3-small`) — primary
2. **Gemini** (`text-embedding-004`) — fallback
3. **Jev** — not yet implemented (raises `NotImplementedError`)

---

## Current Status

### What Works
- ✅ JWT now uses `JWT_SECRET_KEY` (or falls back to `SECRET_KEY`)
- ✅ All 4 LLM providers (Jev, OpenAI, Gemini, Anthropic) are configured
- ✅ Automatic fallback chain: if one fails, tries the next
- ✅ Embeddings from OpenAI or Gemini
- ✅ Model tier mapping for all providers
- ✅ Mock mode for development (no keys needed)

### What You Need to Do
1. Set your preferred provider keys in `.env`:
   - For Jev: `JEV_API_KEY`
   - For OpenAI: `OPENAI_API_KEY`
   - For Gemini: `GEMINI_API_KEY`
   - For Anthropic: `ANTHROPIC_API_KEY`
2. (Optional) Override model names via env vars
3. Install the new dependency: `pip install anthropic==0.44.0`

### Example `.env` for Gemini-First Setup
```bash
# Leave Jev/OpenAI empty to skip them
JEV_API_KEY=
OPENAI_API_KEY=

# Use Gemini as primary
GEMINI_API_KEY=your-gemini-api-key

# Anthropic as fallback
ANTHROPIC_API_KEY=your-anthropic-api-key
```

---

## Testing

To verify which provider is being used:

```python
from packages.llm_gateway.client import get_llm_gateway, LLMRequest, LLMMessage, ModelTier

gateway = get_llm_gateway()
response = gateway.complete(LLMRequest(
    messages=[LLMMessage(role="user", content="Hello")],
    tier=ModelTier.BALANCED,
    temperature=0.7
))
print(f"Provider used: {response.model}")
```

The `response.model` will show the actual model name used (e.g., `gemini-1.5-pro`, `gpt-4o`, `claude-3-5-sonnet-20241022`, or `mock`).
