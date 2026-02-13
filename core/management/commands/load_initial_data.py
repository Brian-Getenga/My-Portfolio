from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import SiteSettings, Skill, Experience, Education, Certification, Project, Service
from taggit.models import Tag

class Command(BaseCommand):
    help = "Seed initial real-world data into the portfolio database"

    def handle(self, *args, **options):
        # Create superuser if not exists
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("✅ Created admin user (admin/admin123)"))

        # === Site Settings ===
        site, _ = SiteSettings.objects.get_or_create(
            site_name="Brian Getenga Portfolio",
            defaults={
                "tagline": "Crafting Digital Excellence",
                "about_me": (
                    "<p>Passionate software developer specializing in Django, "
                    "machine learning, and scalable systems. I love turning complex "
                    "problems into elegant solutions.</p>"
                ),
                "email": "briangetenga3@gmail.com",
                "location": "Nairobi, Kenya",
                "github_url": "https://github.com/brian-getenga",
                "linkedin_url": "https://linkedin.com/in/briangetenga",
                "years_experience": 4,
                "projects_completed": 50,
                "happy_clients": 30,
            },
        )
        self.stdout.write(self.style.SUCCESS("✅ Site settings created/updated"))

        # === Skills ===
        skills = [
            ("Python", "backend", 95, "fab fa-python"),
            ("Django", "backend", 90, "fab fa-python"),
            ("React", "frontend", 80, "fab fa-react"),
            ("HTML5", "frontend", 95, "fab fa-html5"),
            ("CSS3", "frontend", 90, "fab fa-css3-alt"),
            ("JavaScript", "frontend", 85, "fab fa-js"),
            ("Docker", "devops", 70, "fab fa-docker"),
            ("PostgreSQL", "database", 80, "fas fa-database"),
            ("Git & GitHub", "tools", 95, "fab fa-git-alt"),
            ("Machine Learning", "other", 85, "fas fa-brain"),
        ]

        for name, cat, prof, icon in skills:
            Skill.objects.get_or_create(
                name=name,
                defaults={
                    "category": cat,
                    "proficiency": prof,
                    "icon_class": icon,
                    "description": f"Proficient in {name} development and integration.",
                },
            )
        self.stdout.write(self.style.SUCCESS("✅ Skills seeded"))

        # === Experience ===
        Experience.objects.get_or_create(
            title="Software Developer Intern",
            company="Harambee House, ICT Department",
            start_date="2024-10-01",
            end_date="2024-12-31",
            defaults={
                "location": "Nairobi, Kenya",
                "employment_type": "internship",
                "description": "<p>Enhanced network performance and security.</p>",
                "technologies": "Python, Django, Networking, Git",
            },
        )
        Experience.objects.get_or_create(
            title="Web Developer",
            company="Zetech University",
            start_date="2023-01-01",
            end_date="2024-01-01",
            defaults={
                "location": "Nairobi, Kenya",
                "employment_type": "contract",
                "description": "<p>Developed student result management system.</p>",
                "technologies": "Django, HTML, Bootstrap, CSS",
            },
        )
        self.stdout.write(self.style.SUCCESS("✅ Experience seeded"))

        # === Education ===
        Education.objects.get_or_create(
            degree="Bachelor of Science",
            field_of_study="Information Technology",
            institution="Zetech University",
            start_date="2020-01-01",
            end_date="2024-01-01",
            defaults={"description": "Focused on software engineering and networking."},
        )
        Education.objects.get_or_create(
            degree="Short Course",
            field_of_study="CCNA & Ethical Hacking",
            institution="Zetech University",
            start_date="2024-04-01",
            end_date="2024-09-01",
            defaults={"description": "Gained skills in networking and cybersecurity."},
        )
        self.stdout.write(self.style.SUCCESS("✅ Education seeded"))

        # === Certifications ===
        Certification.objects.get_or_create(
            name="CCNA",
            issuing_organization="Cisco",
            issue_date="2024-05-12",
            defaults={"description": "Network installation and troubleshooting."},
        )
        Certification.objects.get_or_create(
            name="Ethical Hacking Training",
            issuing_organization="Zetech University",
            issue_date="2024-09-01",
            defaults={"description": "Practical ethical hacking fundamentals."},
        )
        self.stdout.write(self.style.SUCCESS("✅ Certifications seeded"))

        # === Projects ===
        projects = [
            (
                "Online Pharmacy System",
                "fullstack",
                "Django, PostgreSQL, Bootstrap, JavaScript",
                "Built an online pharmacy platform with secure authentication and prescriptions.",
            ),
            (
                "Portfolio Website",
                "fullstack",
                "Django, HTML, CSS, Bootstrap, JavaScript",
                "Personal portfolio showcasing projects, blogs, and achievements.",
            ),
            (
                "Network Performance Dashboard",
                "backend",
                "Python, Django, REST API, Chart.js",
                "Dashboard for visualizing network metrics and uptime reports.",
            ),
        ]

        for title, cat, tech, desc in projects:
            Project.objects.get_or_create(
                title=title,
                defaults={
                    "category": cat,
                    "description": desc,
                    "full_description": f"<p>{desc}</p>",
                    "technologies": tech,
                    "status": "completed",
                },
            )
        self.stdout.write(self.style.SUCCESS("✅ Projects seeded"))

        # === Tags ===
        tags = ["django", "ml", "ai", "react", "python", "fullstack"]
        for tag in tags:
            Tag.objects.get_or_create(name=tag, slug=tag)
        self.stdout.write(self.style.SUCCESS("✅ Tags added"))

        # === Services ===
        services = [
            ("Web Development", "Building secure, scalable web applications.", "fas fa-laptop-code", 300.00),
            ("Machine Learning Solutions", "AI-driven analytics and prediction tools.", "fas fa-brain", 500.00),
            ("API Development", "RESTful APIs for mobile and web platforms.", "fas fa-cogs", 250.00),
            ("IT Consultation", "Expert advice for tech integration.", "fas fa-headset", 150.00),
        ]

        for title, short_desc, icon, price in services:
            Service.objects.get_or_create(
                title=title,
                defaults={
                    "short_description": short_desc,
                    "description": f"<p>{short_desc}</p>",
                    "icon": icon,
                    "starting_price": price,
                },
            )
        self.stdout.write(self.style.SUCCESS("✅ Services seeded"))

        self.stdout.write(self.style.SUCCESS("🎉 All portfolio data loaded successfully!"))
