from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, F, Count, Avg
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
import hashlib
import secrets
from datetime import timedelta

from .models import (
    Project, BlogPost, Skill, Experience, Education, Certification,
    Testimonial, ContactMessage, Newsletter, SiteSettings, Service, 
    Achievement, FAQ, SocialProof, ProjectGallery, BlogComment
)
from .forms import ContactForm, NewsletterForm, BlogCommentForm


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent string"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request):
    """Get referrer URL"""
    return request.META.get('HTTP_REFERER', '')


class HomeView(TemplateView):
    """Homepage view with all sections - Optimized with caching"""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cache site settings for 1 hour
        site_settings = cache.get('site_settings')
        if not site_settings:
            site_settings = SiteSettings.load()
            cache.set('site_settings', site_settings, 3600)
        
        context['site_settings'] = site_settings
        
        # Featured projects with view counts
        context['featured_projects'] = Project.objects.filter(
            featured=True, 
            status='completed'
        ).select_related().prefetch_related('tags')[:6]
        
        # Skills grouped by category
        skills = Skill.objects.filter(is_active=True).select_related()
        context['skills'] = skills
        context['featured_skills'] = skills.filter(featured=True)[:12]
        
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
        }
        
        return context


class ProjectListView(ListView):
    """List all projects with advanced filtering"""
    model = Project
    template_name = 'core/projects.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Project.objects.filter(status='completed').select_related().prefetch_related('tags')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(technologies__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()
        
        # Sort
        sort_by = self.request.GET.get('sort', '-views')
        if sort_by in ['-views', '-created_at', 'title', '-likes']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        
        # Get all tags
        all_tags = set()
        for project in Project.objects.filter(status='completed'):
            all_tags.update(project.tags.names())
        context['all_tags'] = sorted(all_tags)
        
        # Categories
        context['categories'] = Project.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_sort'] = self.request.GET.get('sort', '-views')
        
        return context


class ProjectDetailView(DetailView):
    """Individual project detail with analytics tracking"""
    model = Project
    template_name = 'core/project_detail.html'
    context_object_name = 'project'
    
    def get_object(self):
        obj = get_object_or_404(
            Project.objects.select_related().prefetch_related('tags', 'gallery_images', 'testimonials'),
            slug=self.kwargs['slug']
        )
        
        # Increment views (use F() to avoid race conditions)
        Project.objects.filter(pk=obj.pk).update(views=F('views') + 1)
        obj.refresh_from_db()
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        
        # Related projects based on tags and category
        related = Project.objects.filter(
            status='completed'
        ).exclude(id=self.object.id)
        
        # Try to find projects with matching tags first
        if self.object.tags.exists():
            related = related.filter(
                tags__in=self.object.tags.all()
            ).distinct()[:3]
        
        # If not enough, fill with same category
        if related.count() < 3:
            category_related = Project.objects.filter(
                status='completed',
                category=self.object.category
            ).exclude(id=self.object.id)[:3]
            related = list(related) + list(category_related)
            related = related[:3]
        
        context['related_projects'] = related
        
        # Project testimonials
        context['project_testimonials'] = self.object.testimonials.filter(is_approved=True)
        
        return context


class BlogListView(ListView):
    """List all blog posts with advanced filtering"""
    model = BlogPost
    template_name = 'core/blog.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('tags')
        
        # Filter by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(content__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()
        
        # Sort
        sort_by = self.request.GET.get('sort', '-published_date')
        if sort_by in ['-published_date', '-views', 'title', '-likes']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        
        # Get all tags
        all_tags = set()
        for post in BlogPost.objects.filter(status='published'):
            all_tags.update(post.tags.names())
        context['all_tags'] = sorted(all_tags)
        
        # Featured posts
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            featured=True
        )[:3]
        
        # Popular posts
        context['popular_posts'] = BlogPost.objects.filter(
            status='published'
        ).order_by('-views')[:5]
        
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_sort'] = self.request.GET.get('sort', '-published_date')
        
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
        
        # Increment views
        BlogPost.objects.filter(pk=obj.pk).update(views=F('views') + 1)
        obj.refresh_from_db()
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        
        # Related posts based on tags
        related = BlogPost.objects.filter(
            status='published'
        ).exclude(id=self.object.id)
        
        if self.object.tags.exists():
            related = related.filter(
                tags__in=self.object.tags.all()
            ).distinct()[:3]
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
        
        # Reading progress
        context['show_reading_progress'] = True
        
        return context


@require_POST
def blog_comment_submit(request, slug):
    """Handle blog comment submission"""
    post = get_object_or_404(BlogPost, slug=slug, status='published', allow_comments=True)
    form = BlogCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.ip_address = get_client_ip(request)
        
        # Auto-approve if email matches author or trusted domain
        author_email = post.author.email if post.author else None
        if comment.email == author_email or comment.email.endswith('@trusted-domain.com'):
            comment.is_approved = True
        
        comment.save()
        
        # Send notification email
        try:
            subject = f"New comment on '{post.title}'"
            message = f"""
            New comment from {comment.name} ({comment.email}):
            
            {comment.content}
            
            {'Approved automatically' if comment.is_approved else 'Pending approval'}
            
            View: {request.build_absolute_uri(post.get_absolute_url())}
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except:
            pass
        
        if comment.is_approved:
            messages.success(request, 'Your comment has been posted!')
        else:
            messages.info(request, 'Your comment is awaiting moderation.')
    else:
        messages.error(request, 'Please correct the errors in your comment.')
    
    return redirect(post.get_absolute_url() + '#comments')


def contact_view(request):
    """Handle contact form submission with spam protection"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        # Honeypot spam protection
        if request.POST.get('website'):  # Honeypot field
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
                messages.error(request, 'Too many submissions. Please try again later.')
                return redirect('contact')
            
            contact.save()
            
            # Send detailed notification to admin
            try:
                site_settings = SiteSettings.load()
                
                # HTML email
                html_content = render_to_string('emails/contact_notification.html', {
                    'contact': contact,
                    'site_settings': site_settings,
                })
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=f"🔔 New Contact: {contact.subject}",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.ADMIN_EMAIL],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                
                # Send confirmation to user
                user_html = render_to_string('emails/contact_confirmation.html', {
                    'contact': contact,
                    'site_settings': site_settings,
                })
                user_text = strip_tags(user_html)
                
                user_email = EmailMultiAlternatives(
                    subject=f"Thank you for contacting {site_settings.site_name}",
                    body=user_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[contact.email],
                )
                user_email.attach_alternative(user_html, "text/html")
                user_email.send(fail_silently=True)
                
                messages.success(request, '✅ Message sent successfully! I\'ll respond within 24 hours.')
            except Exception as e:
                messages.success(request, 'Your message has been saved. I will respond shortly.')
                print(f"Email error: {e}")
            
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {
        'form': form,
        'site_settings': SiteSettings.load()
    })


@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription with double opt-in"""
    form = NewsletterForm(request.POST)
    
    if form.is_valid():
        email = form.cleaned_data['email']
        name = form.cleaned_data.get('name', '')
        
        # Check if already subscribed
        existing = Newsletter.objects.filter(email=email).first()
        
        if existing and existing.is_active:
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
            site_settings = SiteSettings.load()
            verification_url = request.build_absolute_uri(
                f'/newsletter/verify/{newsletter.verification_token}/'
            )
            
            html_content = render_to_string('emails/newsletter_welcome.html', {
                'newsletter': newsletter,
                'site_settings': site_settings,
                'verification_url': verification_url,
            })
            text_content = strip_tags(html_content)
            
            email_message = EmailMultiAlternatives(
                subject=f"Welcome to {site_settings.site_name} Newsletter! 🎉",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[newsletter.email],
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=True)
        except Exception as e:
            print(f"Newsletter email error: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully subscribed! Check your email to verify.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@require_GET
def newsletter_verify(request, token):
    """Verify newsletter subscription"""
    newsletter = get_object_or_404(Newsletter, verification_token=token)
    newsletter.is_verified = True
    newsletter.verification_token = ''
    newsletter.save()
    
    messages.success(request, '✅ Email verified! You\'re now subscribed to the newsletter.')
    return redirect('home')


@require_GET
def newsletter_unsubscribe(request, email):
    """Unsubscribe from newsletter"""
    newsletter = get_object_or_404(Newsletter, email=email)
    newsletter.is_active = False
    newsletter.unsubscribed_at = timezone.now()
    newsletter.save()
    
    return render(request, 'core/newsletter_unsubscribe.html', {
        'site_settings': SiteSettings.load()
    })


def download_resume(request):
    """Download resume/CV file with analytics"""
    site_settings = SiteSettings.load()
    
    if site_settings.resume_file:
        # Track download
        cache_key = f"resume_download_{get_client_ip(request)}"
        if not cache.get(cache_key):
            # Log download event here if you have analytics
            cache.set(cache_key, True, 3600)  # Prevent duplicate counts for 1 hour
        
        response = HttpResponse(site_settings.resume_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{site_settings.site_name.replace(" ", "_")}_Resume.pdf"'
        return response
    else:
        messages.error(request, 'Resume file not available.')
        return redirect('home')


def search_view(request):
    """Global search functionality with ranking"""
    query = request.GET.get('q', '').strip()
    
    context = {
        'query': query,
        'site_settings': SiteSettings.load(),
    }
    
    if query:
        # Projects
        projects = Project.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(technologies__icontains=query) |
            Q(tags__name__icontains=query),
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
            Q(description__icontains=query),
            is_active=True
        )[:5]
        
        context.update({
            'projects': projects,
            'posts': posts,
            'services': services,
            'total_results': projects.count() + posts.count() + services.count(),
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
    project = get_object_or_404(Project, slug=slug)
    
    # Check if already liked (using session)
    liked_projects = request.session.get('liked_projects', [])
    
    if project.id in liked_projects:
        return JsonResponse({
            'success': False,
            'message': 'Already liked',
            'likes': project.likes
        })
    
    # Increment likes
    Project.objects.filter(pk=project.pk).update(likes=F('likes') + 1)
    project.refresh_from_db()
    
    # Store in session
    liked_projects.append(project.id)
    request.session['liked_projects'] = liked_projects
    
    return JsonResponse({
        'success': True,
        'likes': project.likes
    })


@require_POST
def blog_like(request, slug):
    """Like a blog post (AJAX)"""
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Check if already liked
    liked_posts = request.session.get('liked_posts', [])
    
    if post.id in liked_posts:
        return JsonResponse({
            'success': False,
            'message': 'Already liked',
            'likes': post.likes
        })
    
    # Increment likes
    BlogPost.objects.filter(pk=post.pk).update(likes=F('likes') + 1)
    post.refresh_from_db()
    
    # Store in session
    liked_posts.append(post.id)
    request.session['liked_posts'] = liked_posts
    
    return JsonResponse({
        'success': True,
        'likes': post.likes
    })


def services_view(request):
    """Services page"""
    services = Service.objects.filter(is_active=True)
    
    return render(request, 'core/services.html', {
        'services': services,
        'site_settings': SiteSettings.load(),
    })


def service_detail(request, slug):
    """Individual service detail"""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    
    # Related services
    related_services = Service.objects.filter(
        is_active=True
    ).exclude(id=service.id)[:3]
    
    return render(request, 'core/service_detail.html', {
        'service': service,
        'related_services': related_services,
        'site_settings': SiteSettings.load(),
        'contact_form': ContactForm(initial={'subject': f'Inquiry about {service.title}'}),
    })


def about_view(request):
    """About page with full bio"""
    return render(request, 'core/about.html', {
        'site_settings': SiteSettings.load(),
        'skills': Skill.objects.filter(is_active=True),
        'experiences': Experience.objects.all(),
        'education': Education.objects.all(),
        'certifications': Certification.objects.all(),
        'achievements': Achievement.objects.all(),
    })


def error_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', {
        'site_settings': SiteSettings.load(),
    }, status=404)


def error_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', {
        'site_settings': SiteSettings.load(),
    }, status=500)