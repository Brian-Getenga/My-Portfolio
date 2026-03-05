"""
STATS INITIALIZATION & VERIFICATION GUIDE
==========================================

To ensure your stats are working correctly and pulling from the database:

1. RUN THE INITIALIZATION COMMAND:
   python manage.py init_site_settings
   
   This will:
   - Create SiteSettings if it doesn't exist
   - Initialize with default values (0 as base)
   - Display current values in the terminal

2. UPDATE STATS VIA DJANGO ADMIN:
   - Navigate to: /admin/core/sitesettings/
   - Edit the SiteSettings record (there should be only one)
   - Update these fields:
     * Years Experience: 4+
     * Happy Clients: 30+
     * Coffee Consumed: 1000+
   - Save and refresh your page to see changes

3. VERIFY DATABASE VALUES:
   Use the Django shell to check current values:
   
   python manage.py shell
   >>> from core.models import SiteSettings
   >>> s = SiteSettings.load()
   >>> print(f"Years Experience: {s.years_experience}")
   >>> print(f"Happy Clients: {s.happy_clients}")
   >>> print(f"Coffee Consumed: {s.coffee_consumed}")
   >>> exit()

4. DATABASE STATS MAPPING:
   
   Stats on homepage pull from:
   - Years Experience    → SiteSettings.years_experience
   - Projects Shipped    → Project.objects.filter(status='completed').count()
   - Happy Clients       → SiteSettings.happy_clients
   - Coffees Brewed      → SiteSettings.coffee_consumed

5. HOW IT WORKS:
   - View (core/views.py) queries the database
   - Passes stats as context to template
   - Template displays with data-countup attribute
   - JavaScript (CountUp.js) animates the numbers on scroll

6. TROUBLESHOOTING:
   If stats still show 0+:
   a) Run: python manage.py shell
   b) Execute: SiteSettings.objects.all().delete()
   c) Run: python manage.py init_site_settings
   d) Update values in /admin/core/sitesettings/
   e) Clear cache: python manage.py shell
   f) In shell: from django.core.cache import cache; cache.clear()
"""

from django.core.management.base import BaseCommand
from core.models import SiteSettings, Project, BlogPost, Skill
from django.db.models import Sum


class Command(BaseCommand):
    help = "Verify and display current stats from database"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n📊 STATS VERIFICATION REPORT\n'))
        
        try:
            site_settings = SiteSettings.load()
            
            # Database stats
            completed_projects = Project.objects.filter(status='completed').count()
            published_posts = BlogPost.objects.filter(status='published').count()
            total_views = Project.objects.aggregate(total=Sum('views'))['total'] or 0
            active_techs = Skill.objects.filter(is_active=True).count()
            
            self.stdout.write(self.style.SUCCESS('✓ Database Values:\n'))
            self.stdout.write(f"  Years Experience:   {site_settings.years_experience}")
            self.stdout.write(f"  Happy Clients:      {site_settings.happy_clients}")
            self.stdout.write(f"  Coffee Consumed:    {site_settings.coffee_consumed}")
            
            self.stdout.write(self.style.SUCCESS('\n✓ Computed Values:\n'))
            self.stdout.write(f"  Projects Shipped:   {completed_projects}")
            self.stdout.write(f"  Blog Posts:         {published_posts}")
            self.stdout.write(f"  Total Views:        {total_views}")
            self.stdout.write(f"  Active Skills:      {active_techs}")
            
            self.stdout.write(self.style.SUCCESS('\n✓ What appears on homepage:\n'))
            self.stdout.write(f"  {site_settings.years_experience}+ Years Experience")
            self.stdout.write(f"  {completed_projects}+ Projects Shipped")
            self.stdout.write(f"  {site_settings.happy_clients}+ Happy Clients")
            self.stdout.write(f"  {site_settings.coffee_consumed}☕ Coffees Brewed")
            
            self.stdout.write(self.style.SUCCESS('\n✓ To update these values:\n'))
            self.stdout.write("  1. Go to: /admin/core/sitesettings/")
            self.stdout.write("  2. Edit the SiteSettings record")
            self.stdout.write("  3. Update required fields")
            self.stdout.write("  4. Save and refresh page\n")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Error: {e}\n')
            )
            self.stdout.write(
                self.style.WARNING('Run this first: python manage.py init_site_settings\n')
            )
