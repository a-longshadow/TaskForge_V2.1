"""
TaskForge URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from apps.core.views import health_check, home, system_stats

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core app URLs
    path('', home, name='home'),
    path('health/', lambda r: HttpResponse("OK"), name='health'),  # Guaranteed 200 for Railway
    path('ready/', health_check, name='health_check'),  # Deeper health check
    path('stats/', system_stats, name='system_stats'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.handler404'
handler500 = 'apps.core.views.handler500' 