"""
Tests for Brian Getenga Portfolio
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import (
    SiteSettings, Project, BlogPost, Skill, Experience,
    Testimonial, ContactMessage, Newsletter, Service
)


class SiteSettingsTestCase(TestCase):
    """Test Site Settings model"""
    
    def setUp(self):
        self.settings = SiteSettings.load()
    
    def test_singleton_pattern(self):
        """Test that only one SiteSettings instance exists"""
        settings1 = SiteSettings.load()
        settings2 = SiteSettings.load()
        self.assertEqual(settings1.id, settings2.id)
    
    def test_default_values(self):
        """Test default values are set"""
        self.assertEqual(self.settings.site_name, "Brian Getenga Portfolio")
        self.assertEqual(self.settings.years_experience, 4)


class ProjectTestCase(TestCase):
    """Test Project model"""
    
    def setUp(self):
        self.project = Project.objects.create(
            title="Test Project",
            description="Test Description",
            full_description="Full test description",
            technologies="Python, Django, React",
            status="completed"
        )
    
    def test_project_creation(self):
        """Test project is created correctly"""
        self.assertEqual(self.project.title, "Test Project")
        self.assertEqual(self.project.status, "completed")
    
    def test_slug_generation(self):
        """Test slug is auto-generated"""
        self.assertEqual(self.project.slug, "test-project")
    
    def test_tech_list(self):
        """Test technology list parsing"""
        tech_list = self.project.tech_list
        self.assertEqual(len(tech_list), 3)
        self.assertIn("Python", tech_list)


class BlogPostTestCase(TestCase):
    """Test BlogPost model"""
    
    def setUp(self):
        self.post = BlogPost.objects.create(
            title="Test Post",
            excerpt="Test excerpt",
            content="Test content",
            author="Brian Getenga",
            status="published"
        )
    
    def test_post_creation(self):
        """Test blog post is created correctly"""
        self.assertEqual(self.post.title, "Test Post")
        self.assertEqual(self.post.status, "published")
    
    def test_slug_generation(self):
        """Test slug is auto-generated"""
        self.assertEqual(self.post.slug, "test-post")
    
    def test_published_date_auto_set(self):
        """Test published date is set automatically"""
        self.assertIsNotNone(self.post.published_date)


class ViewsTestCase(TestCase):
    """Test views"""
    
    def setUp(self):
        self.client = Client()
        self.settings = SiteSettings.load()
    
    def test_home_page(self):
        """Test home page loads"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
    
    def test_projects_page(self):
        """Test projects page loads"""
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/projects.html')
    
    def test_blog_page(self):
        """Test blog page loads"""
        response = self.client.get(reverse('blog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/blog.html')
    
    def test_contact_page(self):
        """Test contact page loads"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')


class ContactFormTestCase(TestCase):
    """Test contact form"""
    
    def setUp(self):
        self.client = Client()
    
    def test_contact_form_submission(self):
        """Test contact form can be submitted"""
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Test message'
        })
        
        # Should redirect after successful submission
        self.assertEqual(response.status_code, 302)
        
        # Check message was saved
        self.assertEqual(ContactMessage.objects.count(), 1)
        message = ContactMessage.objects.first()
        self.assertEqual(message.name, 'Test User')
        self.assertEqual(message.email, 'test@example.com')


class NewsletterTestCase(TestCase):
    """Test newsletter subscription"""
    
    def setUp(self):
        self.client = Client()
    
    def test_newsletter_subscription(self):
        """Test newsletter subscription works"""
        response = self.client.post(
            reverse('newsletter_subscribe'),
            {'email': 'test@example.com'},
            content_type='application/json'
        )
        
        # Check subscription was created
        self.assertEqual(Newsletter.objects.count(), 1)
        subscription = Newsletter.objects.first()
        self.assertEqual(subscription.email, 'test@example.com')
        self.assertTrue(subscription.is_active)
    
    def test_duplicate_subscription(self):
        """Test duplicate email is rejected"""
        Newsletter.objects.create(email='test@example.com', is_active=True)
        
        response = self.client.post(
            reverse('newsletter_subscribe'),
            {'email': 'test@example.com'},
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)


class AdminTestCase(TestCase):
    """Test admin interface"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
    
    def test_admin_login(self):
        """Test admin can login"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_project_list(self):
        """Test admin can view projects"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/admin/core/project/')
        self.assertEqual(response.status_code, 200)


class SEOTestCase(TestCase):
    """Test SEO features"""
    
    def setUp(self):
        self.client = Client()
    
    def test_sitemap_exists(self):
        """Test sitemap is accessible"""
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
    
    def test_meta_tags(self):
        """Test meta tags are present"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, '<meta name="description"')
        self.assertContains(response, '<meta name="keywords"')


class PerformanceTestCase(TestCase):
    """Test performance features"""
    
    def test_static_files(self):
        """Test static files are configured"""
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'STATIC_URL'))
        self.assertTrue(hasattr(settings, 'STATIC_ROOT'))
    
    def test_media_files(self):
        """Test media files are configured"""
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'MEDIA_URL'))
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))


class SecurityTestCase(TestCase):
    """Test security features"""
    
    def test_csrf_protection(self):
        """Test CSRF protection is enabled"""
        from django.conf import settings
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE
        )
    
    def test_xss_protection(self):
        """Test XSS protection"""
        from django.conf import settings
        if not settings.DEBUG:
            self.assertTrue(settings.SECURE_BROWSER_XSS_FILTER)


# Run tests with:
# python manage.py test
