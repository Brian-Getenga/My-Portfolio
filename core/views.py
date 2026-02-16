from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, F, Count, Avg, Prefetch
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.urls import reverse
import hashlib
import secrets
from datetime import timedelta
import logging

from .models import (
    Project, BlogPost, Skill, Experience, Education, Certification,
    Testimonial, ContactMessage, Newsletter, SiteSettings, Service, 
    Achievement, FAQ, SocialProof, ProjectGallery, BlogComment
)
from .forms import ContactForm, NewsletterForm, BlogCommentForm

# Setup logging
logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address with proper forwarding support"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_user_agent(request):
    """Get user agent string"""
    return request.META.get('HTTP_USER_AGENT', '')[:255]


def get_referrer(request):
    """Get referrer URL"""
    return request.META.get('HTTP_REFERER', '')[:255]


def get_site_settings():
    """Get site settings with caching"""
    cache_key = 'site_settings_v1'
    site_settings = cache.get(cache_key)
    
    if not site_settings:
        try:
            site_settings = SiteSettings.load()
            cache.set(cache_key, site_settings, 3600)  # Cache for 1 hour
        except Exception as e:
            logger.error(f"Error loading site settings: {e}")
            site_settings = None
    
    return site_settings


class HomeView(TemplateView):
    """Homepage view with all sections - Optimized with caching"""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Site settings
            context['site_settings'] = get_site_settings()
            
            # Featured projects with optimized queries
            context['featured_projects'] = Project.objects.filter(
                featured=True, 
                status='completed'
            ).select_related().prefetch_related('tags')[:6]
            
            # Skills grouped by category with caching
            cache_key = 'skills_data_v1'
            skills_data = cache.get(cache_key)
            
            if not skills_data:
                skills = Skill.objects.filter(is_active=True).select_related()
                skills_data = {
                    'all': list(skills),
                    'featured': list(skills.filter(featured=True)[:12])
                }
                cache.set(cache_key, skills_data, 1800)  # 30 minutes
            
            context['skills'] = skills_data['all']
            context['featured_skills'] = skills_data['featured']
            
            # Recent experiences
            context['experiences'] = Experience.objects.select_related()[:4]
            
            # Education
            context['education'] = Education.objects.all()[:3]
            
            # Certifications
            context['certifications'] = Certification.objects.all()[:6]
            
            # Featured testimonials
            context['testimonials'] = Testimonial.objects.filter(
                is_featured=True,
                is_approved=True
            ).select_related('project')[:6]
            
            # Active services
            context['services'] = Service.objects.filter(is_active=True)
            context['featured_services'] = Service.objects.filter(
                is_active=True, 
                featured=True
            )[:3]
            
            # Recent achievements
            context['achievements'] = Achievement.objects.all()[:6]
            
            # Recent blog posts
            context['recent_posts'] = BlogPost.objects.filter(
                status='published'
            ).select_related('author').prefetch_related('tags')[:3]
            
            # Social proof metrics
            context['social_proof'] = SocialProof.objects.filter(is_active=True)
            
            # FAQs
            context['faqs'] = FAQ.objects.filter(is_active=True)[:5]
            
            # Forms
            context['contact_form'] = ContactForm()
            context['newsletter_form'] = NewsletterForm()
            
            # Stats
            context['stats'] = {
                'total_projects': Project.objects.filter(status='completed').count(),
                'total_blog_posts': BlogPost.objects.filter(status='published').count(),
                'total_views': Project.objects.aggregate(total=Count('views'))['total'] or 0,
                'total_clients': context['site_settings'].happy_clients if context['site_settings'] else 50,
                'total_technologies': Skill.objects.filter(is_active=True).count(),
            }
            
        except Exception as e:
            logger.error(f"Error in HomeView: {e}")
            messages.error(self.request, "Some content failed to load. Please refresh the page.")
        
        return context


class ProjectListView(ListView):
    """List all projects with advanced filtering and pagination"""
    model = Project
    template_name = 'core/projects.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        try:
            queryset = Project.objects.filter(
                status='completed'
            ).select_related().prefetch_related('tags', 'gallery_images')
            
            # Filter by category
            category = self.request.GET.get('category', '').strip()
            if category and category in dict(Project.CATEGORY_CHOICES):
                queryset = queryset.filter(category=category)
            
            # Filter by tag
            tag = self.request.GET.get('tag', '').strip()
            if tag:
                queryset = queryset.filter(tags__slug__iexact=tag)
            
            # Search with better matching
            search = self.request.GET.get('search', '').strip()
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(full_description__icontains=search) |
                    Q(technologies__icontains=search) |
                    Q(tags__name__icontains=search) |
                    Q(client__icontains=search)
                ).distinct()
            
            # Sort with validation
            sort_by = self.request.GET.get('sort', '-views').strip()
            valid_sorts = ['-views', '-created_at', 'title', '-title', '-likes', '-featured']
            if sort_by in valid_sorts:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-views')
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error in ProjectListView queryset: {e}")
            return Project.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['site_settings'] = get_site_settings()
            
            # Get all unique tags with caching
            cache_key = 'project_tags_v1'
            tags = cache.get(cache_key)
            
            if not tags:
                tags = set()
                for project in Project.objects.filter(status='completed').prefetch_related('tags'):
                    tags.update(project.tags.values_list('name', flat=True))
                tags = sorted(tags)
                cache.set(cache_key, tags, 1800)
            
            context['tags'] = tags
            
            # Categories
            context['categories'] = Project.CATEGORY_CHOICES
            context['current_category'] = self.request.GET.get('category', '')
            context['current_tag'] = self.request.GET.get('tag', '')
            context['current_sort'] = self.request.GET.get('sort', '-views')
            
            # Stats
            context['stats'] = {
                'total_projects': Project.objects.filter(status='completed').count(),
                'total_clients': context['site_settings'].happy_clients if context['site_settings'] else 0,
                'total_technologies': Skill.objects.filter(is_active=True).count(),
            }
            
        except Exception as e:
            logger.error(f"Error in ProjectListView context: {e}")
        
        return context


class ProjectDetailView(DetailView):
    """Individual project detail with analytics tracking"""
    model = Project
    template_name = 'core/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        return Project.objects.select_related().prefetch_related(
            'tags', 
            'gallery_images',
            Prefetch('testimonials', queryset=Testimonial.objects.filter(is_approved=True))
        )
    
    def get_object(self):
        obj = super().get_object()
        
        try:
            # Increment views atomically (avoid race conditions)
            Project.objects.filter(pk=obj.pk).update(views=F('views') + 1)
            obj.refresh_from_db()
        except Exception as e:
            logger.error(f"Error incrementing project views: {e}")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['site_settings'] = get_site_settings()
            
            # Related projects with better matching
            related = Project.objects.filter(
                status='completed'
            ).exclude(id=self.object.id)
            
            # Match by tags first
            if self.object.tags.exists():
                related = related.filter(
                    tags__in=self.object.tags.all()
                ).annotate(
                    same_tags_count=Count('tags')
                ).order_by('-same_tags_count', '-views').distinct()[:3]
            
            # Fill with same category if needed
            if len(related) < 3:
                category_related = Project.objects.filter(
                    status='completed',
                    category=self.object.category
                ).exclude(id=self.object.id).order_by('-views')[:3]
                
                existing_ids = [p.id for p in related]
                for proj in category_related:
                    if proj.id not in existing_ids and len(related) < 3:
                        related = list(related) + [proj]
            
            context['related_projects'] = related[:3]
            
            # Check if user has liked this project
            liked_projects = self.request.session.get('liked_projects', [])
            context['user_has_liked'] = self.object.id in liked_projects
            
        except Exception as e:
            logger.error(f"Error in ProjectDetailView context: {e}")
            context['related_projects'] = []
        
        return context


class BlogListView(ListView):
    """List all blog posts with advanced filtering"""
    model = BlogPost
    template_name = 'core/blog.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        try:
            queryset = BlogPost.objects.filter(
                status='published'
            ).select_related('author').prefetch_related('tags')
            
            # Filter by tag
            tag = self.request.GET.get('tag', '').strip()
            if tag:
                queryset = queryset.filter(tags__slug__iexact=tag)
            
            # Search
            search = self.request.GET.get('search', '').strip()
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(excerpt__icontains=search) |
                    Q(content__icontains=search) |
                    Q(tags__name__icontains=search) |
                    Q(author__first_name__icontains=search) |
                    Q(author__last_name__icontains=search)
                ).distinct()
            
            # Sort with validation
            sort_by = self.request.GET.get('sort', '-published_date').strip()
            valid_sorts = ['-published_date', '-views', 'title', '-likes', '-featured']
            if sort_by in valid_sorts:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-published_date')
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error in BlogListView queryset: {e}")
            return BlogPost.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['site_settings'] = get_site_settings()
            
            # Get all tags with caching
            cache_key = 'blog_tags_v1'
            tags = cache.get(cache_key)
            
            if not tags:
                tags = set()
                for post in BlogPost.objects.filter(status='published').prefetch_related('tags'):
                    tags.update(post.tags.values_list('name', flat=True))
                tags = sorted(tags)
                cache.set(cache_key, tags, 1800)
            
            context['tags'] = tags
            
            # Featured post
            featured_post = BlogPost.objects.filter(
                status='published',
                featured=True
            ).first()
            context['featured_post'] = featured_post
            
            # Popular posts
            context['popular_posts'] = BlogPost.objects.filter(
                status='published'
            ).order_by('-views')[:5]
            
            # Recent posts
            context['recent_posts'] = BlogPost.objects.filter(
                status='published'
            ).order_by('-published_date')[:5]
            
            context['current_tag'] = self.request.GET.get('tag', '')
            context['current_sort'] = self.request.GET.get('sort', '-published_date')
            
        except Exception as e:
            logger.error(f"Error in BlogListView context: {e}")
        
        return context


class BlogDetailView(DetailView):
    """Individual blog post with comments"""
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('tags')
    
    def get_object(self):
        obj = super().get_object()
        
        try:
            # Increment views atomically
            BlogPost.objects.filter(pk=obj.pk).update(views=F('views') + 1)
            obj.refresh_from_db()
        except Exception as e:
            logger.error(f"Error incrementing blog post views: {e}")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['site_settings'] = get_site_settings()
            
            # Related posts
            related = BlogPost.objects.filter(
                status='published'
            ).exclude(id=self.object.id)
            
            if self.object.tags.exists():
                related = related.filter(
                    tags__in=self.object.tags.all()
                ).annotate(
                    same_tags_count=Count('tags')
                ).order_by('-same_tags_count', '-published_date').distinct()[:3]
            else:
                related = related.order_by('-published_date')[:3]
            
            context['related_posts'] = related
            
            # Comments
            if self.object.allow_comments:
                context['comments'] = self.object.comments.filter(
                    is_approved=True,
                    parent__isnull=True
                ).select_related('parent').prefetch_related('replies')
                context['comment_form'] = BlogCommentForm()
            
            # Check if user has liked this post
            liked_posts = self.request.session.get('liked_posts', [])
            context['user_has_liked'] = self.object.id in liked_posts
            
        except Exception as e:
            logger.error(f"Error in BlogDetailView context: {e}")
            context['related_posts'] = []
        
        return context


@require_POST
def blog_comment_submit(request, slug):
    """Handle blog comment submission with spam protection"""
    try:
        post = get_object_or_404(
            BlogPost, 
            slug=slug, 
            status='published', 
            allow_comments=True
        )
        
        # Honeypot spam protection
        if request.POST.get('website'):
            return redirect(post.get_absolute_url() + '#comments')
        
        form = BlogCommentForm(request.POST)
        
        if form.is_valid():
            # Rate limiting - max 3 comments per IP per hour
            ip_address = get_client_ip(request)
            recent_comments = BlogComment.objects.filter(
                ip_address=ip_address,
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            if recent_comments >= 3:
                messages.error(request, 'Too many comments. Please try again later.')
                return redirect(post.get_absolute_url() + '#comments')
            
            comment = form.save(commit=False)
            comment.post = post
            comment.ip_address = ip_address
            
            # Auto-approve if email matches author or trusted domain
            author_email = post.author.email if post.author else None
            if (comment.email == author_email or 
                comment.email.endswith('@trusted-domain.com') or
                comment.email.endswith(getattr(settings, 'TRUSTED_EMAIL_DOMAIN', '@example.com'))):
                comment.is_approved = True
            
            comment.save()
            
            # Send notification email
            try:
                site_settings = get_site_settings()
                subject = f"New comment on '{post.title}'"
                
                html_content = f"""
                <h2>New Comment</h2>
                <p><strong>From:</strong> {comment.name} ({comment.email})</p>
                <p><strong>Post:</strong> {post.title}</p>
                <p><strong>Comment:</strong></p>
                <p>{comment.content}</p>
                <p><strong>Status:</strong> {'Approved' if comment.is_approved else 'Pending approval'}</p>
                <p><a href="{request.build_absolute_uri(post.get_absolute_url())}">View post</a></p>
                """
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=True)
                
            except Exception as e:
                logger.error(f"Error sending comment notification: {e}")
            
            if comment.is_approved:
                messages.success(request, '✅ Your comment has been posted!')
            else:
                messages.info(request, '📝 Your comment is awaiting moderation.')
        else:
            messages.error(request, 'Please correct the errors in your comment.')
            
    except Exception as e:
        logger.error(f"Error in blog_comment_submit: {e}")
        messages.error(request, 'An error occurred. Please try again.')
    
    return redirect(post.get_absolute_url() + '#comments')


def contact_view(request):
    """Handle contact form submission with enhanced spam protection"""
    site_settings = get_site_settings()
    
    if request.method == 'POST':
        try:
            form = ContactForm(request.POST)
            
            # Honeypot spam protection
            if request.POST.get('website'):
                return redirect('home')
            
            if form.is_valid():
                contact = form.save(commit=False)
                contact.ip_address = get_client_ip(request)
                contact.user_agent = get_user_agent(request)
                contact.referrer = get_referrer(request)
                
                # Rate limiting - max 3 submissions per IP per hour
                recent_count = ContactMessage.objects.filter(
                    ip_address=contact.ip_address,
                    created_at__gte=timezone.now() - timedelta(hours=1)
                ).count()
                
                if recent_count >= 3:
                    messages.error(request, '⚠️ Too many submissions. Please try again later.')
                    return redirect('contact')
                
                contact.save()
                
                # Send notification emails
                try:
                    # Admin notification
                    admin_subject = f"🔔 New Contact: {contact.subject}"
                    admin_html = render_to_string('emails/contact_notification.html', {
                        'contact': contact,
                        'site_settings': site_settings,
                    })
                    admin_text = strip_tags(admin_html)
                    
                    admin_email = EmailMultiAlternatives(
                        admin_subject,
                        admin_text,
                        settings.DEFAULT_FROM_EMAIL,
                        [getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')],
                    )
                    admin_email.attach_alternative(admin_html, "text/html")
                    admin_email.send(fail_silently=False)
                    
                    # User confirmation
                    user_subject = f"Thank you for contacting {site_settings.site_name if site_settings else 'us'}"
                    user_html = render_to_string('emails/contact_confirmation.html', {
                        'contact': contact,
                        'site_settings': site_settings,
                    })
                    user_text = strip_tags(user_html)
                    
                    user_email = EmailMultiAlternatives(
                        user_subject,
                        user_text,
                        settings.DEFAULT_FROM_EMAIL,
                        [contact.email],
                    )
                    user_email.attach_alternative(user_html, "text/html")
                    user_email.send(fail_silently=True)
                    
                    messages.success(request, '✅ Message sent successfully! I\'ll respond within 24 hours.')
                    
                except Exception as e:
                    logger.error(f"Email error in contact_view: {e}")
                    messages.success(request, '✅ Your message has been saved. I will respond shortly.')
                
                return redirect('home')
            else:
                messages.error(request, '❌ Please correct the errors below.')
                
        except Exception as e:
            logger.error(f"Error in contact_view: {e}")
            messages.error(request, 'An error occurred. Please try again.')
    else:
        # Pre-fill service if coming from service page
        initial_data = {}
        service_slug = request.GET.get('service')
        if service_slug:
            try:
                service = Service.objects.get(slug=service_slug, is_active=True)
                initial_data['subject'] = f'Inquiry about {service.title}'
            except Service.DoesNotExist:
                pass
        
        form = ContactForm(initial=initial_data)
    
    # Get FAQs
    faqs = FAQ.objects.filter(is_active=True)[:6]
    
    return render(request, 'core/contact.html', {
        'form': form,
        'site_settings': site_settings,
        'faqs': faqs,
    })


@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription with double opt-in"""
    try:
        form = NewsletterForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data.get('name', '')
            
            # Check if already subscribed and active
            existing = Newsletter.objects.filter(email=email).first()
            
            if existing and existing.is_active and existing.is_verified:
                return JsonResponse({
                    'success': False,
                    'message': 'You are already subscribed!'
                })
            
            # Create or reactivate subscription
            if existing:
                newsletter = existing
                newsletter.is_active = True
                newsletter.name = name or newsletter.name
            else:
                newsletter = form.save(commit=False)
                newsletter.ip_address = get_client_ip(request)
                newsletter.source = request.GET.get('source', 'website')
            
            # Generate verification token
            newsletter.verification_token = secrets.token_urlsafe(32)
            newsletter.save()
            
            # Send welcome/verification email
            try:
                site_settings = get_site_settings()
                verification_url = request.build_absolute_uri(
                    reverse('newsletter_verify', args=[newsletter.verification_token])
                )
                
                html_content = render_to_string('emails/newsletter_welcome.html', {
                    'newsletter': newsletter,
                    'site_settings': site_settings,
                    'verification_url': verification_url,
                })
                text_content = strip_tags(html_content)
                
                email_message = EmailMultiAlternatives(
                    subject=f"Welcome to {site_settings.site_name if site_settings else 'our'} Newsletter! 🎉",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[newsletter.email],
                )
                email_message.attach_alternative(html_content, "text/html")
                email_message.send(fail_silently=True)
                
            except Exception as e:
                logger.error(f"Newsletter email error: {e}")
            
            return JsonResponse({
                'success': True,
                'message': '✅ Successfully subscribed! Check your email to verify.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email address',
                'errors': form.errors
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error in newsletter_subscribe: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


@require_GET
def newsletter_verify(request, token):
    """Verify newsletter subscription"""
    try:
        newsletter = get_object_or_404(Newsletter, verification_token=token)
        newsletter.is_verified = True
        newsletter.is_active = True
        newsletter.verification_token = ''
        newsletter.save()
        
        messages.success(request, '✅ Email verified! You\'re now subscribed to the newsletter.')
    except Exception as e:
        logger.error(f"Error in newsletter_verify: {e}")
        messages.error(request, 'Invalid verification link.')
    
    return redirect('home')


@require_GET
def newsletter_unsubscribe(request, email):
    """Unsubscribe from newsletter"""
    try:
        newsletter = get_object_or_404(Newsletter, email=email)
        newsletter.is_active = False
        newsletter.unsubscribed_at = timezone.now()
        newsletter.save()
        
        return render(request, 'core/newsletter_unsubscribe.html', {
            'site_settings': get_site_settings(),
            'success': True,
        })
    except Exception as e:
        logger.error(f"Error in newsletter_unsubscribe: {e}")
        return render(request, 'core/newsletter_unsubscribe.html', {
            'site_settings': get_site_settings(),
            'success': False,
        })


def download_resume(request):
    """Download resume/CV file with analytics"""
    try:
        site_settings = get_site_settings()
        
        if site_settings and site_settings.resume_file:
            # Track download (prevent duplicates with caching)
            cache_key = f"resume_download_{get_client_ip(request)}"
            if not cache.get(cache_key):
                cache.set(cache_key, True, 3600)  # 1 hour
            
            # Return file
            response = FileResponse(
                site_settings.resume_file.open('rb'),
                content_type='application/pdf'
            )
            filename = f"{site_settings.site_name.replace(' ', '_')}_Resume.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, '❌ Resume file not available.')
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Error in download_resume: {e}")
        messages.error(request, 'An error occurred downloading the resume.')
        return redirect('home')


def search_view(request):
    """Global search functionality with ranking"""
    query = request.GET.get('q', '').strip()
    
    context = {
        'query': query,
        'site_settings': get_site_settings(),
    }
    
    if query and len(query) >= 2:  # Minimum search length
        try:
            # Projects
            projects = Project.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(full_description__icontains=query) |
                Q(technologies__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(client__icontains=query),
                status='completed'
            ).distinct()[:10]
            
            # Blog posts
            posts = BlogPost.objects.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query),
                status='published'
            ).distinct()[:10]
            
            # Services
            services = Service.objects.filter(
                Q(title__icontains=query) |
                Q(short_description__icontains=query) |
                Q(description__icontains=query) |
                Q(technologies__icontains=query),
                is_active=True
            )[:5]
            
            context.update({
                'projects': projects,
                'posts': posts,
                'services': services,
                'total_results': projects.count() + posts.count() + services.count(),
            })
            
        except Exception as e:
            logger.error(f"Error in search_view: {e}")
            context.update({
                'projects': Project.objects.none(),
                'posts': BlogPost.objects.none(),
                'services': Service.objects.none(),
                'total_results': 0,
            })
    else:
        context.update({
            'projects': Project.objects.none(),
            'posts': BlogPost.objects.none(),
            'services': Service.objects.none(),
            'total_results': 0,
        })
    
    return render(request, 'core/search_results.html', context)


@require_POST
def project_like(request, slug):
    """Like a project (AJAX)"""
    try:
        project = get_object_or_404(Project, slug=slug)
        
        # Check if already liked (using session)
        liked_projects = request.session.get('liked_projects', [])
        
        if project.id in liked_projects:
            return JsonResponse({
                'success': False,
                'message': 'Already liked',
                'likes': project.likes,
                'action': 'already_liked'
            })
        
        # Increment likes atomically
        Project.objects.filter(pk=project.pk).update(likes=F('likes') + 1)
        project.refresh_from_db()
        
        # Store in session
        liked_projects.append(project.id)
        request.session['liked_projects'] = liked_projects
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'likes': project.likes,
            'action': 'liked'
        })
        
    except Exception as e:
        logger.error(f"Error in project_like: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        }, status=500)


@require_POST
def blog_like(request, slug):
    """Like a blog post (AJAX)"""
    try:
        post = get_object_or_404(BlogPost, slug=slug, status='published')
        
        # Check if already liked
        liked_posts = request.session.get('liked_posts', [])
        
        if post.id in liked_posts:
            return JsonResponse({
                'success': False,
                'message': 'Already liked',
                'likes': post.likes,
                'action': 'already_liked'
            })
        
        # Increment likes atomically
        BlogPost.objects.filter(pk=post.pk).update(likes=F('likes') + 1)
        post.refresh_from_db()
        
        # Store in session
        liked_posts.append(post.id)
        request.session['liked_posts'] = liked_posts
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'likes': post.likes,
            'action': 'liked'
        })
        
    except Exception as e:
        logger.error(f"Error in blog_like: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        }, status=500)


def services_view(request):
    """Services page with all features"""
    try:
        site_settings = get_site_settings()
        services = Service.objects.filter(is_active=True).order_by('-featured', 'order', 'title')
        
        # Get testimonials for services
        testimonials = Testimonial.objects.filter(
            is_approved=True,
            is_featured=True
        )[:6]
        
        # Get FAQs
        faqs = FAQ.objects.filter(is_active=True)[:6]
        
        # Process steps (can be customized)
        process_steps = [
            'Consultation',
            'Planning',
            'Development',
            'Launch'
        ]
        
        return render(request, 'core/services.html', {
            'services': services,
            'site_settings': site_settings,
            'testimonials': testimonials,
            'faqs': faqs,
            'process_steps': process_steps,
        })
        
    except Exception as e:
        logger.error(f"Error in services_view: {e}")
        return render(request, 'core/services.html', {
            'services': Service.objects.none(),
            'site_settings': get_site_settings(),
        })

def service_detail(request, slug):
    """Individual service detail"""
    try:
        service = get_object_or_404(Service, slug=slug, is_active=True)
        site_settings = get_site_settings()
        
        # Related services
        related_services = Service.objects.filter(
            is_active=True
        ).exclude(id=service.id).order_by('-featured', '?')[:3]
        
        # Get general testimonials (not service-specific since model doesn't have that relationship)
        testimonials = Testimonial.objects.filter(
            is_approved=True,
            is_featured=True
        )[:3]
        
        # Get general FAQs (not service-specific)
        faqs = FAQ.objects.filter(is_active=True)[:6]
        
        # Contact form with pre-filled subject
        initial_data = {'subject': f'Inquiry about {service.title}'}
        contact_form = ContactForm(initial=initial_data)
        
        return render(request, 'core/service_detail.html', {
            'service': service,
            'related_services': related_services,
            'testimonials': testimonials,
            'faqs': faqs,
            'site_settings': site_settings,
            'contact_form': contact_form,
        })
        
    except Exception as e:
        logger.error(f"Error in service_detail: {e}")
        messages.error(request, 'Service not found.')
        return redirect('services')
    
    
def about_view(request):
    """About page with full bio"""
    try:
        return render(request, 'core/about.html', {
            'site_settings': get_site_settings(),
            'skills': Skill.objects.filter(is_active=True).order_by('category', '-proficiency'),
            'experiences': Experience.objects.all().order_by('-is_current', '-start_date'),
            'education': Education.objects.all().order_by('-is_current', '-start_date'),
            'certifications': Certification.objects.all().order_by('-issue_date'),
            'achievements': Achievement.objects.all().order_by('-date_achieved'),
        })
    except Exception as e:
        logger.error(f"Error in about_view: {e}")
        return render(request, 'core/about.html', {
            'site_settings': get_site_settings(),
        })


def error_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', {
        'site_settings': get_site_settings(),
    }, status=404)


def error_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', {
        'site_settings': get_site_settings(),
    }, status=500)