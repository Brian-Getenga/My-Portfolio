from django.core.management.base import BaseCommand
from core.models import SiteSettings


class Command(BaseCommand):
    """
    Initialize or reset SiteSettings singleton with proper database values.
    Usage: python manage.py init_site_settings
    """
    help = "Initialize SiteSettings with defaults if not exists, or reset to database defaults"

    def handle(self, *args, **options):
        site_settings, created = SiteSettings.objects.get_or_create(
            pk=1,  # Singleton pattern
            defaults={
                'site_name': 'Brian Getenga Portfolio',
                'site_description': 'Professional Full Stack Developer',
                'tagline': 'Crafting Digital Excellence in Code & Craft',
                'email': 'briangetenga3@gmail.com',
                'location': 'Nairobi, Kenya',
                'timezone': 'Africa/Nairobi',
                'years_experience': 4,
                'happy_clients': 30,
                'coffee_consumed': 1000,
                'projects_completed': 50,
                'code_commits': 5000,
                'available_for_work': True,
                'available_for_freelance': True,
                'enable_blog': True,
                'enable_newsletter': True,
                'enable_testimonials': True,
                'enable_dark_mode': True,
                'maintenance_mode': False,
                'footer_text': '© 2024 Brian Getenga. All rights reserved.',
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ SiteSettings initialized successfully!\n\n'
                    f'  Years Experience: {site_settings.years_experience}\n'
                    f'  Happy Clients: {site_settings.happy_clients}\n'
                    f'  Coffee Consumed: {site_settings.coffee_consumed}\n'
                    f'  Projects Completed: {site_settings.projects_completed}\n'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠ SiteSettings already exists.\n\n'
                    f'  Current Values:\n'
                    f'  Years Experience: {site_settings.years_experience}\n'
                    f'  Happy Clients: {site_settings.happy_clients}\n'
                    f'  Coffee Consumed: {site_settings.coffee_consumed}\n'
                    f'  Projects Completed: {site_settings.projects_completed}\n'
                )
            )
