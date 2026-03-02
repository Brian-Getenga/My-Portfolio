from .models import Service
from .views import get_site_settings


def global_context(request):
    """
    Global template context available on all pages.

    Provides:
    - site_settings: singleton SiteSettings instance (cached via get_site_settings)
    - footer_services: up to 6 active services for footer navigation
    """
    return {
        "footer_services": Service.objects.filter(is_active=True).order_by(
            "-featured", "order"
        )[:6],
        "site_settings": get_site_settings(),
    }

from .models import SiteSettings


def site_settings(request):
    """Make site settings available in all templates"""
    return {
        'site_settings': SiteSettings.load(),
    }
