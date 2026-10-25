# SchedularOS API Routes — Complete Router Configuration

## Root URL Config (`schedularos/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('core.auth_urls')),
    path('api/v1/', include('core.urls')),
    path('api/v1/', include('orchestration.urls')),
    path('api/v1/', include('proposals.urls')),
    path('api/v1/', include('agents_api.urls')),
    path('api/v1/', include('analytics.urls')),
    path('api/v1/', include('conversations.urls')),
    path('api/v1/', include('tasks_api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

## 1. Auth (`core/auth_urls.py`)

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from core.models import UserProfile, Organization

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register, name='register'),
    path('me/', me, name='me'),
]
```

**Endpoints:**
- `POST /api/v1/auth/token/` — Login (JWT)
- `POST /api/v1/auth/token/refresh/` — Refresh JWT
- `POST /api/v1/auth/register/` — Register (creates org + user with role='admin')
- `GET /api/v1/auth/me/` — Current user profile

---

## 2. Core (`core/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    OrganizationViewSet,
    BrandViewSet,
    UserProfileViewSet,
    LeadViewSet,
    ResearchViewSet,
    WorkflowViewSet,
    KnowledgeViewSet,
)
from core import webhooks

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'research', ResearchViewSet, basename='research')
router.register(r'langgraph', WorkflowViewSet, basename='workflow')
router.register(r'knowledge', KnowledgeViewSet, basename='knowledge')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/whatsapp/', webhooks.whatsapp_webhook, name='whatsapp_webhook'),
    path('webhooks/whatsapp/verify/', webhooks.whatsapp_verify, name='whatsapp_verify'),
]
```

**Endpoints:**
- `GET/POST /api/v1/organizations/` — Org CRUD
- `GET /api/v1/organizations/me/` — Current org
- `GET/POST /api/v1/brands/` — Brand CRUD
- `GET /api/v1/profiles/` — List org members
- `GET /api/v1/profiles/me/` — Current user profile
- `GET/POST /api/v1/leads/` — Lead CRUD (filter `?stage=`)
- `POST /api/v1/research/perform/` — Run research (market/competitors/audience)
- `POST /api/v1/langgraph/run/` — Standalone LangGraph run
- `POST /api/v1/knowledge/store/` — Store doc in RAG
- `POST /api/v1/knowledge/search/` — Search RAG
- `POST /api/v1/webhooks/whatsapp/` — WhatsApp webhook
- `GET /api/v1/webhooks/whatsapp/verify/` — WhatsApp verify

---

## 3. Orchestration (`orchestration/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orchestration.views import WorkflowRunViewSet, RunStepViewSet

router = DefaultRouter()
router.register(r'workflows', WorkflowRunViewSet, basename='workflowrun')
router.register(r'steps', RunStepViewSet, basename='runstep')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `GET/POST /api/v1/workflows/` — WorkflowRun CRUD
- `POST /api/v1/workflows/launch/` — Launch workflow from goal
- `POST /api/v1/workflows/{id}/cancel/` — Cancel workflow
- `POST /api/v1/workflows/{id}/pause/` — Pause workflow
- `POST /api/v1/workflows/{id}/resume/` — Resume workflow
- `GET /api/v1/steps/` — List RunSteps (filter `?run=`)
- `GET /api/v1/steps/{id}/` — Get RunStep

---

## 4. Proposals (`proposals/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from proposals.views import ProposalViewSet

router = DefaultRouter()
router.register(r'proposals', ProposalViewSet, basename='proposal')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `GET/POST /api/v1/proposals/` — Proposal CRUD (filter `?status=`)
- `GET /api/v1/proposals/{id}/` — Get proposal
- `POST /api/v1/proposals/{id}/decide/` — Approve/reject/edit proposal

---

## 5. Agents (`agents_api/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from agents_api.views import AgentViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `GET /api/v1/agents/` — List registered agents
- `POST /api/v1/agents/run/` — Run single agent ad-hoc

---

## 6. Analytics (`analytics/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from analytics.views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `GET /api/v1/analytics/kpis/` — KPI dashboard
- `GET /api/v1/analytics/lead_trend/` — Lead trend over time
- `GET /api/v1/analytics/funnel/` — Funnel by stage
- `GET /api/v1/analytics/lead_sources/` — Lead sources (by tags)
- `GET /api/v1/analytics/lead_score_distribution/` — Score buckets
- `GET /api/v1/analytics/agent_productivity/` — Agent productivity
- `GET /api/v1/analytics/workflow_stats/` — Workflow stats
- `GET /api/v1/analytics/proposal_stats/` — Proposal stats
- `GET /api/v1/analytics/spend_over_time/` — Spend over time
- `GET /api/v1/analytics/activity/` — Audit events
- `GET /api/v1/analytics/message_trend/` — Message trend (inbound/outbound)
- `GET /api/v1/analytics/trust/` — Trust levels
- `GET /api/v1/analytics/ad_campaigns/` — Live Meta campaigns
- `GET /api/v1/analytics/integrations/` — Integration status

---

## 7. Conversations (`conversations/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from conversations.views import ConversationViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `GET /api/v1/conversations/` — List conversations (inbox)
- `GET /api/v1/conversations/{id}/` — Get conversation
- `GET /api/v1/conversations/{id}/messages/` — Get messages

---

## 8. Tasks (`tasks_api/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tasks_api.views import TaskViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Endpoints:**
- `POST /api/v1/tasks/leads/{lead_id}/score/` — Score lead
- `POST /api/v1/tasks/leads/{lead_id}/tag/` — Tag lead
- `POST /api/v1/tasks/conversations/{conv_id}/reply/` — Reply to conversation
- `POST /api/v1/tasks/advertising/campaigns/` — Create ad campaign
- `POST /api/v1/tasks/advertising/campaign-status/` — Set campaign status
- `POST /api/v1/tasks/followups/schedule/` — Schedule follow-up
- `POST /api/v1/tasks/creative/generate/` — Generate creative
- `POST /api/v1/tasks/campaigns/launch/` — Launch multi-platform campaign
- `GET /api/v1/tasks/pipeline/` — Lead pipeline aggregates

---

## Summary

All endpoints are protected by `IsAuthenticated` except:
- `POST /api/v1/auth/register/` — `AllowAny`
- `POST /api/v1/auth/token/` — `AllowAny`
- `POST /api/v1/auth/token/refresh/` — `AllowAny`
- `POST /api/v1/webhooks/whatsapp/` — `AllowAny` (webhook)
- `GET /api/v1/webhooks/whatsapp/verify/` — `AllowAny` (webhook verify)
