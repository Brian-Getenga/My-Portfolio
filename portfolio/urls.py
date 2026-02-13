"""
URL Configuration for Brian Getenga Portfolio
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import (
    StaticViewSitemap, ProjectSitemap, BlogPostSitemap
)

# Sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'blog': BlogPostSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site headers
admin.site.site_header = "Brian Getenga Portfolio Admin"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Welcome to Portfolio Administration"
