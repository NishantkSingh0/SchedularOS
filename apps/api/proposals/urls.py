from django.urls import path, include
from rest_framework.routers import DefaultRouter
from proposals.views import ProposalViewSet

router = DefaultRouter()
router.register(r'proposals', ProposalViewSet, basename='proposal')

urlpatterns = [
    path('', include(router.urls)),
]
