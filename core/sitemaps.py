from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Project, BlogPost


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'monthly'
    
    def items(self):
        return ['home', 'projects', 'blog', 'contact']
    
    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    """Sitemap for projects"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Project.objects.filter(status='completed')
    
    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    """Sitemap for blog posts"""
    changefreq = 'daily'
    priority = 0.9
    
    def items(self):
        return BlogPost.objects.filter(status='published')
    
    def lastmod(self, obj):
        return obj.updated_at
