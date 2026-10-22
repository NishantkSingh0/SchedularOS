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
