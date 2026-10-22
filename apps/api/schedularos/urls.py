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
