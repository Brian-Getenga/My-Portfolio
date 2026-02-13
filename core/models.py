from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from django.utils import timezone
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SiteSettings(models.Model):
    """Global site settings - Singleton model"""
    # Basic Information
    site_name = models.CharField(max_length=100, default="Brian Getenga Portfolio")
    site_description = models.TextField(default="Professional Full Stack Developer")
    tagline = models.CharField(max_length=200, default="Crafting Digital Excellence", 
                               help_text="Short catchy tagline")
    about_me = RichTextUploadingField()
    profile_image = models.ImageField(upload_to='profile/', null=True, blank=True)
    resume_file = models.FileField(upload_to='resume/', null=True, blank=True,
                                   validators=[FileExtensionValidator(['pdf'])])
    
    # Contact Information
    email = models.EmailField(default="briangetenga3@gmail.com")
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, default="Nairobi, Kenya")
    timezone = models.CharField(max_length=50, default="Africa/Nairobi")
    
    # Social Media Links
    github_url = models.URLField(blank=True, verbose_name="GitHub URL")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter/X URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    youtube_url = models.URLField(blank=True, verbose_name="YouTube URL")
    behance_url = models.URLField(blank=True, verbose_name="Behance URL")
    dribbble_url = models.URLField(blank=True, verbose_name="Dribbble URL")
    
    # Statistics
    years_experience = models.IntegerField(default=4)
    projects_completed = models.IntegerField(default=50)
    happy_clients = models.IntegerField(default=30)
    coffee_consumed = models.IntegerField(default=1000, help_text="Cups of coffee")
    code_commits = models.IntegerField(default=5000, help_text="GitHub commits")
    
    # SEO & Analytics
    meta_keywords = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True, help_text="GA4 Measurement ID")
    google_site_verification = models.CharField(max_length=100, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # Features
    enable_blog = models.BooleanField(default=True)
    enable_newsletter = models.BooleanField(default=True)
    enable_testimonials = models.BooleanField(default=True)
    enable_dark_mode = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)
    
    # Status
    available_for_work = models.BooleanField(default=True)
    available_for_freelance = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text="USD per hour")
    
    # Footer
    footer_text = models.TextField(blank=True, default="© 2024 Brian Getenga. All rights reserved.")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        
        # Optimize profile image
        if self.profile_image:
            img = Image.open(self.profile_image)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize to 500x500
            output_size = (500, 500)
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Replace the image
            self.profile_image = InMemoryUploadedFile(
                output, 'ImageField', f"{self.profile_image.name.split('.')[0]}.jpg",
                'image/jpeg', sys.getsizeof(output), None
            )
        
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Skill(TimeStampedModel):
    """Skills and technologies"""
    CATEGORY_CHOICES = [
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('database', 'Database'),
        ('devops', 'DevOps & Cloud'),
        ('mobile', 'Mobile Development'),
        ('design', 'Design & UI/UX'),
        ('tools', 'Tools & Software'),
        ('soft_skills', 'Soft Skills'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    icon_class = models.CharField(max_length=100, help_text="FontAwesome icon class (e.g., fab fa-python)")
    icon_image = models.ImageField(upload_to='skills/', null=True, blank=True,
                                   help_text="Optional: Custom icon image")
    proficiency = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Proficiency level (0-100)"
    )
    description = models.TextField(blank=True, help_text="Brief description of skill")
    years_experience = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    order = models.IntegerField(default=0, help_text="Display order", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False, help_text="Show on homepage")
    
    class Meta:
        ordering = ['-featured', 'order', 'name']
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Experience(TimeStampedModel):
    """Work experience entries"""
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    company_url = models.URLField(blank=True, help_text="Company website")
    company_logo = models.ImageField(upload_to='companies/', null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ], default='full_time')
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for current position")
    description = RichTextUploadingField()
    achievements = models.TextField(help_text="One achievement per line", blank=True)
    technologies = models.CharField(max_length=500, blank=True, help_text="Comma-separated list")
    order = models.IntegerField(default=0, db_index=True)
    is_current = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        ordering = ['-is_current', '-start_date', 'order']
        verbose_name = "Experience"
        verbose_name_plural = "Experience"
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def duration(self):
        end = self.end_date or timezone.now().date()
        delta = end - self.start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        
        if years > 0:
            return f"{years} year{'s' if years > 1 else ''} {months} month{'s' if months > 1 else ''}"
        return f"{months} month{'s' if months > 1 else ''}"
    
    @property
    def tech_list(self):
        return [tech.strip() for tech in self.technologies.split(',')] if self.technologies else []


class Education(TimeStampedModel):
    """Education history"""
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    institution_url = models.URLField(blank=True)
    institution_logo = models.ImageField(upload_to='institutions/', null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True, help_text="GPA or grade")
    description = models.TextField(blank=True)
    achievements = models.TextField(blank=True, help_text="One per line")
    is_current = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_current', '-start_date', 'order']
        verbose_name = "Education"
        verbose_name_plural = "Education"
    
    def __str__(self):
        return f"{self.degree} - {self.institution}"


class Certification(TimeStampedModel):
    """Professional certifications"""
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True, verbose_name="Verification URL")
    certificate_image = models.ImageField(upload_to='certificates/', null=True, blank=True)
    description = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='certifications')
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-issue_date', 'order']
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
    
    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class Project(TimeStampedModel):
    """Portfolio projects"""
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
        ('planned', 'Planned'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('web_app', 'Web Application'),
        ('mobile_app', 'Mobile Application'),
        ('api', 'API/Backend'),
        ('frontend', 'Frontend'),
        ('fullstack', 'Full Stack'),
        ('design', 'Design'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='web_app')
    description = models.TextField()
    full_description = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='projects/')
    thumbnail = models.ImageField(upload_to='projects/thumbnails/', null=True, blank=True)
    
    # Project Details
    technologies = models.CharField(max_length=500, help_text="Comma-separated list")
    github_url = models.URLField(blank=True, verbose_name="GitHub URL")
    live_url = models.URLField(blank=True, verbose_name="Live Demo URL")
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo demo video")
    client = models.CharField(max_length=200, blank=True)
    client_url = models.URLField(blank=True)
    project_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length=50, blank=True, help_text="e.g., 3 months")
    team_size = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=100, blank=True, help_text="Your role in the project")
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    order = models.IntegerField(default=0, db_index=True)
    views = models.IntegerField(default=0, db_index=True)
    likes = models.IntegerField(default=0)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-featured', 'order', '-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        indexes = [
            models.Index(fields=['status', 'featured']),
            models.Index(fields=['-views']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Create thumbnail if not exists
        if self.featured_image and not self.thumbnail:
            img = Image.open(self.featured_image)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            output_size = (400, 300)
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            self.thumbnail = InMemoryUploadedFile(
                output, 'ImageField', f"thumb_{self.featured_image.name.split('/')[-1]}",
                'image/jpeg', sys.getsizeof(output), None
            )
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug': self.slug})
    
    @property
    def tech_list(self):
        return [tech.strip() for tech in self.technologies.split(',')]


class ProjectGallery(models.Model):
    """Gallery images for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Project Gallery Image"
        verbose_name_plural = "Project Gallery Images"
    
    def __str__(self):
        return f"{self.project.title} - Image {self.order}"


class BlogPost(TimeStampedModel):
    """Blog posts and articles"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=200)
    excerpt = models.TextField(max_length=300)
    content = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='blog/')
    
    # Metadata
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    published_date = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False, db_index=True)
    views = models.IntegerField(default=0, db_index=True)
    reading_time = models.IntegerField(default=5, help_text="Estimated reading time in minutes")
    likes = models.IntegerField(default=0)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(blank=True, help_text="Canonical URL if republished")
    
    # Engagement
    allow_comments = models.BooleanField(default=True)
    
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=['status', 'published_date']),
            models.Index(fields=['-views']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        
        # Auto-calculate reading time from content
        if self.content:
            words = len(self.content.split())
            self.reading_time = max(1, round(words / 200))  # Average reading speed
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})


class BlogComment(TimeStampedModel):
    """Comments on blog posts"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='replies')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"


class Testimonial(TimeStampedModel):
    """Client testimonials"""
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    company_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='testimonials')
    video_url = models.URLField(blank=True, help_text="Video testimonial")
    is_featured = models.BooleanField(default=False, db_index=True)
    is_approved = models.BooleanField(default=True)
    order = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
    
    def __str__(self):
        return f"{self.name} - {self.company}"


class ContactMessage(TimeStampedModel):
    """Contact form submissions"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    budget = models.CharField(max_length=50, blank=True, help_text="Project budget range")
    timeline = models.CharField(max_length=50, blank=True, help_text="Expected timeline")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False, db_index=True)
    is_responded = models.BooleanField(default=False, db_index=True)
    response_date = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [
            models.Index(fields=['is_read', 'is_responded']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class Newsletter(TimeStampedModel):
    """Newsletter subscriptions"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    verification_token = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True, help_text="Where they subscribed from")
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"
    
    def __str__(self):
        return self.email


class Achievement(TimeStampedModel):
    """Awards and achievements"""
    CATEGORY_CHOICES = [
        ('award', 'Award'),
        ('certification', 'Certification'),
        ('milestone', 'Milestone'),
        ('recognition', 'Recognition'),
        ('publication', 'Publication'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='award')
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="FontAwesome icon class")
    image = models.ImageField(upload_to='achievements/', null=True, blank=True)
    date_achieved = models.DateField(db_index=True)
    issuer = models.CharField(max_length=200, blank=True)
    verification_url = models.URLField(blank=True)
    order = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        ordering = ['-date_achieved', 'order']
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
    
    def __str__(self):
        return self.title


class Service(TimeStampedModel):
    """Services offered"""
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(max_length=200)
    description = RichTextUploadingField()
    icon = models.CharField(max_length=100, help_text="FontAwesome icon class")
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text="Starting price in USD")
    deliverables = models.TextField(blank=True, help_text="One per line")
    process_steps = models.TextField(blank=True, help_text="One per line")
    order = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Service"
        verbose_name_plural = "Services"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class FAQ(TimeStampedModel):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=300)
    answer = RichTextUploadingField()
    category = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


class SocialProof(TimeStampedModel):
    """Social proof metrics and badges"""
    METRIC_CHOICES = [
        ('clients', 'Happy Clients'),
        ('projects', 'Projects Completed'),
        ('experience', 'Years of Experience'),
        ('rating', 'Client Rating'),
        ('response', 'Response Time'),
        ('custom', 'Custom Metric'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_CHOICES)
    value = models.CharField(max_length=50, help_text="e.g., 100+, 5.0, 24hrs")
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Social Proof"
        verbose_name_plural = "Social Proof Metrics"
    
    def __str__(self):
        return f"{self.label}: {self.value}"


class AnalyticsSnapshot(models.Model):
    """Daily analytics snapshots"""
    date = models.DateField(unique=True, auto_now_add=True)
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    blog_views = models.IntegerField(default=0)
    project_views = models.IntegerField(default=0)
    contact_submissions = models.IntegerField(default=0)
    newsletter_signups = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Analytics Snapshot"
        verbose_name_plural = "Analytics Snapshots"
    
    def __str__(self):
        return f"Analytics for {self.date}"