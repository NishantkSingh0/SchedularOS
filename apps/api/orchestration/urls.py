from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orchestration.views import WorkflowRunViewSet, RunStepViewSet

router = DefaultRouter()
router.register(r'workflows', WorkflowRunViewSet, basename='workflowrun')
router.register(r'steps', RunStepViewSet, basename='runstep')

urlpatterns = [
    path('', include(router.urls)),
]
