"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from tasks.views import custom_404_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
]

handler404 = 'tasks.views.custom_404_view'

if settings.DEBUG:
    # Catch-all for debug mode so user sees the premium 404 page
    urlpatterns += [re_path(r'^.*$', custom_404_view, {'exception': Exception('Page not found')})]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
