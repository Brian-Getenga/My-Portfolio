from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone
from .models import (
    SiteSettings, Skill, Experience, Education, Certification, Project, ProjectGallery,
    BlogPost, BlogComment, Testimonial, ContactMessage, Newsletter, Achievement, 
    Service, FAQ, SocialProof, AnalyticsSnapshot
)


# Inline Admins

class ProjectGalleryInline(admin.TabularInline):
    model = ProjectGallery
    extra = 1
    fields = ['image', 'caption', 'order']


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    fields = ['name', 'email', 'content', 'is_approved', 'created_at']
    readonly_fields = ['created_at']
    can_delete = True


# Main Admin Classes

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_description', 'tagline', 'about_me', 
                      'profile_image', 'resume_file')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'location', 'timezone')
        }),
        ('Social Media', {
            'fields': ('github_url', 'linkedin_url', 'twitter_url', 'instagram_url', 
                      'facebook_url', 'youtube_url', 'behance_url', 'dribbble_url'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('years_experience', 'projects_completed', 'happy_clients', 
                      'coffee_consumed', 'code_commits')
        }),
        ('SEO & Analytics', {
            'fields': ('meta_keywords', 'meta_description', 'google_analytics_id', 
                      'google_site_verification', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
        ('Features & Settings', {
            'fields': ('enable_blog', 'enable_newsletter', 'enable_testimonials', 
                      'enable_dark_mode', 'maintenance_mode')
        }),
        ('Work Availability', {
            'fields': ('available_for_work', 'available_for_freelance', 'hourly_rate')
        }),
        ('Footer', {
            'fields': ('footer_text',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return False if SiteSettings.objects.exists() else True
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'proficiency_bar', 'years_experience', 
                   'featured', 'is_active', 'order']
    list_filter = ['category', 'is_active', 'featured']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_active', 'featured']
    ordering = ['-featured', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Icon', {
            'fields': ('icon_class', 'icon_image')
        }),
        ('Level', {
            'fields': ('proficiency', 'years_experience')
        }),
        ('Display Settings', {
            'fields': ('featured', 'is_active', 'order')
        }),
    )
    
    def proficiency_bar(self, obj):
        return format_html(
            '<div style="width:100px;background:#e0e0e0;border-radius:3px;">'
            '<div style="width:{}px;background:#4CAF50;height:20px;border-radius:3px;"></div>'
            '</div>',
            obj.proficiency
        )
    proficiency_bar.short_description = 'Proficiency'


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'employment_type', 'start_date', 
                   'end_date', 'duration_display', 'is_current', 'order']
    list_filter = ['is_current', 'employment_type', 'start_date']
    search_fields = ['title', 'company', 'description', 'technologies']
    list_editable = ['order']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'company_url', 'company_logo', 
                      'employment_type', 'is_current')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'location')
        }),
        ('Details', {
            'fields': ('description', 'achievements', 'technologies')
        }),
        ('Display', {
            'fields': ('order',)
        }),
    )
    
    def duration_display(self, obj):
        return obj.duration
    duration_display.short_description = 'Duration'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['degree', 'field_of_study', 'institution', 'start_date', 
                   'end_date', 'is_current', 'order']
    list_filter = ['is_current', 'start_date']
    search_fields = ['degree', 'field_of_study', 'institution']
    list_editable = ['order']
    date_hierarchy = 'start_date'


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'issuing_organization', 'issue_date', 'expiry_date', 
                   'is_expired_display', 'order']
    list_filter = ['issue_date', 'issuing_organization']
    search_fields = ['name', 'issuing_organization', 'credential_id']
    list_editable = ['order']
    date_hierarchy = 'issue_date'
    filter_horizontal = ['skills']
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color:red;">Expired</span>')
        elif obj.expiry_date:
            return format_html('<span style="color:green;">Valid</span>')
        return format_html('<span style="color:gray;">No Expiry</span>')
    is_expired_display.short_description = 'Status'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'featured', 'views', 
                   'likes', 'created_at', 'order']
    list_filter = ['status', 'category', 'featured', 'created_at']
    search_fields = ['title', 'description', 'technologies', 'client']
    list_editable = ['featured', 'order']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    inlines = [ProjectGalleryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'description', 'full_description')
        }),
        ('Media', {
            'fields': ('featured_image', 'thumbnail', 'video_url')
        }),
        ('Project Details', {
            'fields': ('technologies', 'github_url', 'live_url', 'client', 
                      'client_url', 'status')
        }),
        ('Timeline & Team', {
            'fields': ('project_date', 'duration', 'team_size', 'role')
        }),
        ('Settings', {
            'fields': ('featured', 'order', 'tags')
        }),
        ('SEO', {
            'fields': ('meta_description',)
        }),
        ('Analytics', {
            'fields': ('views', 'likes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['views', 'likes']
    
    actions = ['make_featured', 'remove_featured', 'mark_completed']
    
    def make_featured(self, request, queryset):
        queryset.update(featured=True)
    make_featured.short_description = "Mark selected as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(featured=False)
    remove_featured.short_description = "Remove featured status"
    
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = "Mark as completed"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'featured', 'views', 'likes', 
                   'published_date', 'reading_time']
    list_filter = ['status', 'featured', 'published_date', 'author']
    search_fields = ['title', 'excerpt', 'content']
    list_editable = ['status', 'featured']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    inlines = [BlogCommentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Publishing', {
            'fields': ('status', 'published_date', 'scheduled_date', 'featured', 'allow_comments')
        }),
        ('Categorization', {
            'fields': ('tags',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'canonical_url')
        }),
        ('Analytics', {
            'fields': ('views', 'likes', 'reading_time'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['views', 'likes', 'reading_time']
    
    actions = ['publish_posts', 'unpublish_posts', 'make_featured']
    
    def publish_posts(self, request, queryset):
        queryset.update(status='published', published_date=timezone.now())
    publish_posts.short_description = "Publish selected posts"
    
    def unpublish_posts(self, request, queryset):
        queryset.update(status='draft')
    unpublish_posts.short_description = "Unpublish selected posts"
    
    def make_featured(self, request, queryset):
        queryset.update(featured=True)
    make_featured.short_description = "Mark as featured"


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['name', 'email', 'content', 'post__title']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'
    
    actions = ['approve_comments', 'reject_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        queryset.update(is_approved=False)
    reject_comments.short_description = "Reject selected comments"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'rating_stars', 'project', 'is_featured', 
                   'is_approved', 'order', 'created_at']
    list_filter = ['is_featured', 'is_approved', 'rating', 'created_at']
    search_fields = ['name', 'company', 'content']
    list_editable = ['is_featured', 'is_approved', 'order']
    ordering = ['-is_featured', 'order', '-created_at']
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size:1.2em;">{}</span>', stars)
    rating_stars.short_description = 'Rating'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'priority_badge', 'is_read', 
                   'is_responded', 'created_at']
    list_filter = ['is_read', 'is_responded', 'priority', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read', 'is_responded']
    date_hierarchy = 'created_at'
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'budget', 
                      'timeline', 'ip_address', 'user_agent', 'referrer', 'created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'ip_address')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'budget', 'timeline', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'is_responded', 'response_date', 'created_at')
        }),
        ('Technical Info', {
            'fields': ('user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def priority_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545',
        }
        return format_html(
            '<span style="background-color:{};color:white;padding:3px 8px;'
            'border-radius:3px;font-size:11px;font-weight:bold;">{}</span>',
            colors.get(obj.priority, '#6c757d'),
            obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'
    
    actions = ['mark_read', 'mark_unread', 'mark_responded']
    
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_read.short_description = "Mark as read"
    
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_unread.short_description = "Mark as unread"
    
    def mark_responded(self, request, queryset):
        queryset.update(is_responded=True, response_date=timezone.now())
    mark_responded.short_description = "Mark as responded"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'is_verified', 'source', 
                   'subscribed_at']
    list_filter = ['is_active', 'is_verified', 'source', 'subscribed_at']
    search_fields = ['email', 'name']
    list_editable = ['is_active']
    date_hierarchy = 'subscribed_at'
    readonly_fields = ['subscribed_at', 'unsubscribed_at', 'ip_address']
    
    fieldsets = (
        ('Subscriber Info', {
            'fields': ('email', 'name', 'source', 'ip_address')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'subscribed_at', 'unsubscribed_at')
        }),
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'verify_subscribers', 
              'export_emails']
    
    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False, unsubscribed_at=timezone.now())
    deactivate_subscribers.short_description = "Deactivate selected subscribers"
    
    def verify_subscribers(self, request, queryset):
        queryset.update(is_verified=True)
    verify_subscribers.short_description = "Mark as verified"
    
    def export_emails(self, request, queryset):
        emails = queryset.values_list('email', flat=True)
        return HttpResponse(','.join(emails), content_type='text/plain')
    export_emails.short_description = "Export email addresses"


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'issuer', 'date_achieved', 'order']
    list_filter = ['category', 'date_achieved']
    search_fields = ['title', 'description', 'issuer']
    list_editable = ['order']
    date_hierarchy = 'date_achieved'
    ordering = ['-date_achieved', 'order']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'starting_price', 'is_active', 'featured', 'order']
    list_filter = ['is_active', 'featured']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'featured', 'order']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'order']
    list_filter = ['is_active', 'category']
    search_fields = ['question', 'answer']
    list_editable = ['is_active', 'order']


@admin.register(SocialProof)
class SocialProofAdmin(admin.ModelAdmin):
    list_display = ['label', 'value', 'metric_type', 'is_active', 'order']
    list_filter = ['is_active', 'metric_type']
    list_editable = ['is_active', 'order']


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['date', 'page_views', 'unique_visitors', 'blog_views', 
                   'project_views', 'contact_submissions', 'newsletter_signups']
    list_filter = ['date']
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        return False


# Customize admin site
admin.site.site_header = "🚀 Brian Getenga Portfolio Administration"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Welcome to Your Portfolio Dashboard"

# Custom admin index page stats
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Dashboard stats
        extra_context['total_projects'] = Project.objects.count()
        extra_context['total_blog_posts'] = BlogPost.objects.count()
        extra_context['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        extra_context['pending_comments'] = BlogComment.objects.filter(is_approved=False).count()
        extra_context['active_subscribers'] = Newsletter.objects.filter(is_active=True).count()
        
        return super().index(request, extra_context)