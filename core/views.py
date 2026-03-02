from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, F, Count, Avg, Prefetch, Sum
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_deny
from django.core.signing import Signer, BadSignature
from django.contrib.sitemaps import Sitemap
import hashlib
import secrets
from datetime import timedelta
import logging
import json

from .models import (
    Project, BlogPost, Skill, Experience, Education, Certification,
    Testimonial, ContactMessage, Newsletter, SiteSettings, Service,
    Achievement, FAQ, SocialProof, ProjectGallery, BlogComment,
    AnalyticsSnapshot
)
from .forms import ContactForm, NewsletterForm, BlogCommentForm

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def get_referrer(request):
    return request.META.get('HTTP_REFERER', '')[:500]


def get_site_settings():
    cache_key = 'site_settings_v2'
    obj = cache.get(cache_key)
    if not obj:
        try:
            obj = SiteSettings.load()
            cache.set(cache_key, obj, 3600)
        except Exception as e:
            logger.error(f"SiteSettings load error: {e}")
    return obj


def invalidate_cache(*keys):
    for key in keys:
        cache.delete(key)


def track_page_view(request, page_type=None):
    try:
        today = timezone.now().date()
        snapshot, _ = AnalyticsSnapshot.objects.get_or_create(date=today)
        AnalyticsSnapshot.objects.filter(pk=snapshot.pk).update(
            page_views=F('page_views') + 1,
            **({f'{page_type}_views': F(f'{page_type}_views') + 1} if page_type else {})
        )
    except Exception as e:
        logger.warning(f"Analytics tracking failed: {e}")


def rate_limit_check(request, action, limit=3, window_hours=1):
    ip = get_client_ip(request)
    cache_key = f"rate_{action}_{ip}"
    count = cache.get(cache_key, 0)
    if count >= limit:
        return True
    cache.set(cache_key, count + 1, window_hours * 3600)
    return False


# Profanity / spam filter
PROFANITY_LIST = ['spam', 'casino', 'crypto', 'nft', 'pills', 'viagra', 'lottery', 'winner']

def has_profanity(text):
    lower = text.lower()
    return any(word in lower for word in PROFANITY_LIST)


# ─────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get(self, request, *args, **kwargs):
        track_page_view(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_settings = get_site_settings()
        context['site_settings'] = site_settings

        try:
            context['featured_projects'] = (
                Project.objects.filter(featured=True, status='completed')
                .select_related().prefetch_related('tags', 'gallery_images')[:6]
            )

            skills_cache_key = 'skills_grouped_v2'
            skills_data = cache.get(skills_cache_key)
            if not skills_data:
                skills_qs = Skill.objects.filter(is_active=True).order_by('category', '-proficiency')
                grouped = {}
                for skill in skills_qs:
                    grouped.setdefault(skill.category, []).append(skill)
                skills_data = {
                    'all': list(skills_qs),
                    'featured': list(skills_qs.filter(featured=True)[:12]),
                    'grouped': grouped,
                }
                cache.set(skills_cache_key, skills_data, 1800)

            context.update({
                'skills': skills_data['all'],
                'featured_skills': skills_data['featured'],
                'skills_grouped': skills_data['grouped'],
            })

            context['experiences'] = Experience.objects.select_related().order_by('-is_current', '-start_date')[:4]
            context['education'] = Education.objects.all().order_by('-is_current', '-start_date')[:3]
            context['certifications'] = Certification.objects.all().order_by('-issue_date')[:6]
            context['testimonials'] = (
                Testimonial.objects.filter(is_featured=True, is_approved=True)
                .select_related('project')[:6]
            )
            context['services'] = Service.objects.filter(is_active=True).order_by('-featured', 'order')
            context['featured_services'] = Service.objects.filter(is_active=True, featured=True)[:3]
            context['achievements'] = Achievement.objects.all().order_by('-date_achieved')[:6]
            context['recent_posts'] = (
                BlogPost.objects.filter(status='published')
                .select_related('author').prefetch_related('tags')
                .order_by('-published_date')[:3]
            )
            context['social_proof'] = SocialProof.objects.filter(is_active=True).order_by('order')
            context['faqs'] = FAQ.objects.filter(is_active=True).order_by('order')[:6]
            context['contact_form'] = ContactForm()
            context['newsletter_form'] = NewsletterForm()
            context['stats'] = {
                'total_projects': Project.objects.filter(status='completed').count(),
                'total_blog_posts': BlogPost.objects.filter(status='published').count(),
                'total_views': Project.objects.aggregate(total=Sum('views'))['total'] or 0,
                'total_clients': site_settings.happy_clients if site_settings else 30,
                'total_technologies': Skill.objects.filter(is_active=True).count(),
                'years_experience': site_settings.years_experience if site_settings else 4,
                'coffee_consumed': site_settings.coffee_consumed if site_settings else 1000,
            }

            # JSON-LD structured data
            context['json_ld'] = json.dumps({
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "Brian Getenga",
                "jobTitle": "Full Stack Developer",
                "url": self.request.build_absolute_uri('/'),
                "email": site_settings.email if site_settings else "briangetenga3@gmail.com",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Nairobi",
                    "addressCountry": "KE"
                },
                "sameAs": [s for s in [
                    site_settings.github_url if site_settings else "",
                    site_settings.linkedin_url if site_settings else "",
                    site_settings.twitter_url if site_settings else "",
                ] if s]
            })

        except Exception as e:
            logger.error(f"HomeView error: {e}", exc_info=True)

        return context


# ─────────────────────────────────────────────
# Projects
# ─────────────────────────────────────────────

class ProjectListView(ListView):
    model = Project
    template_name = 'core/projects.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        track_page_view(request, 'project')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        try:
            qs = (
                Project.objects.filter(status='completed')
                .select_related()
                .prefetch_related('tags', 'gallery_images')
            )
            category = self.request.GET.get('category', '').strip()
            if category and category in dict(Project.CATEGORY_CHOICES):
                qs = qs.filter(category=category)

            tag = self.request.GET.get('tag', '').strip()
            if tag:
                qs = qs.filter(tags__slug__iexact=tag)

            search = self.request.GET.get('search', '').strip()
            if search:
                qs = qs.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(technologies__icontains=search) |
                    Q(tags__name__icontains=search) |
                    Q(client__icontains=search)
                ).distinct()

            sort_by = self.request.GET.get('sort', '-created_at').strip()
            valid_sorts = ['-views', '-created_at', 'title', '-title', '-likes', '-featured', '-project_date']
            qs = qs.order_by(sort_by if sort_by in valid_sorts else '-created_at')
            return qs
        except Exception as e:
            logger.error(f"ProjectListView queryset error: {e}")
            return Project.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = get_site_settings()
            cache_key = 'project_tags_v2'
            tags = cache.get(cache_key)
            if not tags:
                from taggit.models import Tag
                tags = list(Tag.objects.filter(
                    project__status='completed'
                ).annotate(project_count=Count('project')).order_by('-project_count')[:20])
                cache.set(cache_key, tags, 1800)
            context['tags'] = tags
            context['categories'] = Project.CATEGORY_CHOICES
            context['current_category'] = self.request.GET.get('category', '')
            context['current_tag'] = self.request.GET.get('tag', '')
            context['current_sort'] = self.request.GET.get('sort', '-created_at')
            context['search_query'] = self.request.GET.get('search', '')
            context['total_projects'] = Project.objects.filter(status='completed').count()
            category_counts = (
                Project.objects.filter(status='completed')
                .values('category')
                .annotate(count=Count('id'))
            )
            context['category_counts'] = {c['category']: c['count'] for c in category_counts}
        except Exception as e:
            logger.error(f"ProjectListView context error: {e}")
        return context


class ProjectDetailView(DetailView):
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
        ip = get_client_ip(self.request)
        view_key = f"proj_view_{obj.pk}_{ip}"
        if not cache.get(view_key):
            Project.objects.filter(pk=obj.pk).update(views=F('views') + 1)
            cache.set(view_key, True, 1800)
            track_page_view(self.request, 'project')
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = get_site_settings()

            # JSON-LD for CreativeWork
            context['json_ld'] = json.dumps({
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "name": self.object.title,
                "description": self.object.description,
                "url": self.request.build_absolute_uri(self.object.get_absolute_url()),
                "dateCreated": str(self.object.created_at.date()),
                "creator": {"@type": "Person", "name": "Brian Getenga"}
            })

            related = []
            if self.object.tags.exists():
                related = list(
                    Project.objects.filter(status='completed')
                    .exclude(id=self.object.id)
                    .filter(tags__in=self.object.tags.all())
                    .annotate(same_tags=Count('tags'))
                    .order_by('-same_tags', '-views')
                    .distinct()[:3]
                )
            if len(related) < 3:
                existing_ids = [p.id for p in related] + [self.object.id]
                extra = list(
                    Project.objects.filter(status='completed', category=self.object.category)
                    .exclude(id__in=existing_ids)
                    .order_by('-views')[:3 - len(related)]
                )
                related += extra

            context['related_projects'] = related[:3]
            liked = self.request.session.get('liked_projects', [])
            context['user_has_liked'] = self.object.id in liked

            qs = Project.objects.filter(status='completed').order_by('-featured', 'order', '-created_at')
            ids = list(qs.values_list('id', flat=True))
            try:
                idx = ids.index(self.object.id)
                context['prev_project'] = qs.filter(id=ids[idx - 1]).first() if idx > 0 else None
                context['next_project'] = qs.filter(id=ids[idx + 1]).first() if idx < len(ids) - 1 else None
            except (ValueError, IndexError):
                context['prev_project'] = context['next_project'] = None

        except Exception as e:
            logger.error(f"ProjectDetailView context error: {e}")
            context['related_projects'] = []
        return context

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response


# ─────────────────────────────────────────────
# Blog
# ─────────────────────────────────────────────

class BlogListView(ListView):
    model = BlogPost
    template_name = 'core/blog.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get(self, request, *args, **kwargs):
        track_page_view(request, 'blog')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        try:
            qs = (
                BlogPost.objects.filter(status='published')
                .select_related('author')
                .prefetch_related('tags')
            )
            tag = self.request.GET.get('tag', '').strip()
            if tag:
                qs = qs.filter(tags__slug__iexact=tag)

            search = self.request.GET.get('search', '').strip()
            if search:
                qs = qs.filter(
                    Q(title__icontains=search) |
                    Q(excerpt__icontains=search) |
                    Q(content__icontains=search) |
                    Q(tags__name__icontains=search)
                ).distinct()

            sort_by = self.request.GET.get('sort', '-published_date').strip()
            valid_sorts = ['-published_date', '-views', 'title', '-likes', '-reading_time']
            qs = qs.order_by(sort_by if sort_by in valid_sorts else '-published_date')
            return qs
        except Exception as e:
            logger.error(f"BlogListView queryset error: {e}")
            return BlogPost.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = get_site_settings()
            cache_key = 'blog_tags_v2'
            tags = cache.get(cache_key)
            if not tags:
                from taggit.models import Tag
                tags = list(Tag.objects.filter(
                    blogpost__status='published'
                ).annotate(post_count=Count('blogpost')).order_by('-post_count')[:20])
                cache.set(cache_key, tags, 1800)
            context['tags'] = tags
            context['featured_post'] = BlogPost.objects.filter(status='published', featured=True).first()
            context['popular_posts'] = BlogPost.objects.filter(status='published').order_by('-views')[:5]
            context['current_tag'] = self.request.GET.get('tag', '')
            context['current_sort'] = self.request.GET.get('sort', '-published_date')
            context['search_query'] = self.request.GET.get('search', '')
            context['newsletter_form'] = NewsletterForm()
        except Exception as e:
            logger.error(f"BlogListView context error: {e}")
        return context


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return (
            BlogPost.objects.filter(status='published')
            .select_related('author')
            .prefetch_related('tags')
        )

    def get_object(self):
        obj = super().get_object()
        ip = get_client_ip(self.request)
        view_key = f"blog_view_{obj.pk}_{ip}"
        if not cache.get(view_key):
            BlogPost.objects.filter(pk=obj.pk).update(views=F('views') + 1)
            cache.set(view_key, True, 1800)
            track_page_view(self.request, 'blog')
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = get_site_settings()

            # JSON-LD for Article
            context['json_ld'] = json.dumps({
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": self.object.title,
                "description": self.object.excerpt,
                "datePublished": str(self.object.published_date),
                "dateModified": str(self.object.updated_at.date()),
                "author": {"@type": "Person", "name": "Brian Getenga"},
                "timeRequired": f"PT{self.object.reading_time}M"
            })

            if self.object.tags.exists():
                related = (
                    BlogPost.objects.filter(status='published')
                    .exclude(id=self.object.id)
                    .filter(tags__in=self.object.tags.all())
                    .annotate(same_tags=Count('tags'))
                    .order_by('-same_tags', '-published_date')
                    .distinct()[:3]
                )
            else:
                related = BlogPost.objects.filter(
                    status='published'
                ).exclude(id=self.object.id).order_by('-published_date')[:3]

            context['related_posts'] = related

            if self.object.allow_comments:
                context['comments'] = (
                    self.object.comments.filter(is_approved=True, parent__isnull=True)
                    .prefetch_related('replies')
                    .select_related()
                )
                context['comment_count'] = self.object.comments.filter(is_approved=True).count()
                context['comment_form'] = BlogCommentForm()

            liked_posts = self.request.session.get('liked_posts', [])
            context['user_has_liked'] = self.object.id in liked_posts
            context['newsletter_form'] = NewsletterForm()

            qs = BlogPost.objects.filter(status='published').order_by('-published_date')
            ids = list(qs.values_list('id', flat=True))
            try:
                idx = ids.index(self.object.id)
                context['prev_post'] = qs.filter(id=ids[idx - 1]).first() if idx > 0 else None
                context['next_post'] = qs.filter(id=ids[idx + 1]).first() if idx < len(ids) - 1 else None
            except (ValueError, IndexError):
                context['prev_post'] = context['next_post'] = None

        except Exception as e:
            logger.error(f"BlogDetailView context error: {e}")
            context['related_posts'] = []
        return context


# ─────────────────────────────────────────────
# Blog Comment
# ─────────────────────────────────────────────

@require_POST
def blog_comment_submit(request, slug):
    try:
        post = get_object_or_404(BlogPost, slug=slug, status='published', allow_comments=True)

        if request.POST.get('website_honeypot'):
            return redirect(post.get_absolute_url() + '#comments')

        if rate_limit_check(request, f'comment_{slug}', limit=5, window_hours=1):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Too many comments. Please wait.'}, status=429)
            messages.error(request, '⏳ Too many comments. Please wait before commenting again.')
            return redirect(post.get_absolute_url() + '#comments')

        form = BlogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.ip_address = get_client_ip(request)

            # Profanity filter
            if has_profanity(form.cleaned_data.get('content', '')):
                comment.is_approved = False

            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    comment.parent = BlogComment.objects.get(pk=parent_id, post=post)
                except BlogComment.DoesNotExist:
                    pass

            trusted_domains = getattr(settings, 'TRUSTED_EMAIL_DOMAINS', [])
            author_email = post.author.email if post.author else None
            email_domain = comment.email.split('@')[-1] if '@' in comment.email else ''
            if comment.email == author_email or email_domain in trusted_domains:
                comment.is_approved = True

            comment.save()

            try:
                site_settings = get_site_settings()
                html = render_to_string('emails/comment_notification.html', {
                    'comment': comment, 'post': post, 'site_settings': site_settings,
                    'post_url': request.build_absolute_uri(post.get_absolute_url()),
                })
                msg = EmailMultiAlternatives(
                    f"💬 New Comment on '{post.title}'",
                    strip_tags(html),
                    settings.DEFAULT_FROM_EMAIL,
                    [getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                )
                msg.attach_alternative(html, 'text/html')
                msg.send(fail_silently=True)
            except Exception as e:
                logger.warning(f"Comment email error: {e}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                status_msg = '✅ Comment posted!' if comment.is_approved else '📝 Comment pending moderation.'
                return JsonResponse({
                    'success': True,
                    'approved': comment.is_approved,
                    'message': status_msg,
                    'comment': {
                        'name': comment.name,
                        'content': comment.content,
                        'created_at': comment.created_at.strftime('%B %d, %Y'),
                        'is_reply': bool(comment.parent),
                    }
                })

            if comment.is_approved:
                messages.success(request, '✅ Your comment has been posted!')
            else:
                messages.info(request, '📝 Your comment is awaiting moderation. Thank you!')
        else:
            error_list = '; '.join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            messages.error(request, f'❌ Please fix the following: {error_list}')

    except Exception as e:
        logger.error(f"blog_comment_submit error: {e}", exc_info=True)
        messages.error(request, '❌ Something went wrong. Please try again.')

    return redirect(post.get_absolute_url() + '#comments')


# ─────────────────────────────────────────────
# Contact
# ─────────────────────────────────────────────

def contact_view(request):
    site_settings = get_site_settings()

    if request.method == 'POST':
        try:
            if request.POST.get('website_honeypot'):
                return redirect('home')

            if rate_limit_check(request, 'contact', limit=3, window_hours=1):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': '⏳ Too many messages. Try again later.'}, status=429)
                messages.error(request, '⏳ Too many messages recently. Please try again in an hour.')
                return redirect('contact')

            form = ContactForm(request.POST)
            if form.is_valid():
                contact = form.save(commit=False)
                contact.ip_address = get_client_ip(request)
                contact.user_agent = get_user_agent(request)
                contact.referrer = get_referrer(request)
                contact.save()

                try:
                    today = timezone.now().date()
                    snapshot, _ = AnalyticsSnapshot.objects.get_or_create(date=today)
                    AnalyticsSnapshot.objects.filter(pk=snapshot.pk).update(
                        contact_submissions=F('contact_submissions') + 1
                    )
                except Exception:
                    pass

                try:
                    admin_html = render_to_string('emails/contact_notification.html', {
                        'contact': contact, 'site_settings': site_settings,
                    })
                    admin_msg = EmailMultiAlternatives(
                        f"🔔 New Contact: {contact.subject} [{contact.priority.upper()}]",
                        strip_tags(admin_html),
                        settings.DEFAULT_FROM_EMAIL,
                        [getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                    )
                    admin_msg.attach_alternative(admin_html, 'text/html')
                    admin_msg.send(fail_silently=False)

                    user_html = render_to_string('emails/contact_confirmation.html', {
                        'contact': contact, 'site_settings': site_settings,
                    })
                    user_msg = EmailMultiAlternatives(
                        f"Thanks for reaching out, {contact.name.split()[0]}! 👋",
                        strip_tags(user_html),
                        settings.DEFAULT_FROM_EMAIL,
                        [contact.email],
                    )
                    user_msg.attach_alternative(user_html, 'text/html')
                    user_msg.send(fail_silently=True)

                    messages.success(request, f'✅ Message sent! I typically respond within 24 hours, {contact.name.split()[0]}.')
                except Exception as e:
                    logger.error(f"Contact email error: {e}")
                    messages.success(request, "✅ Message received! I'll get back to you shortly.")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
                return redirect('home')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
                messages.error(request, '❌ Please correct the highlighted fields.')

        except Exception as e:
            logger.error(f"contact_view error: {e}", exc_info=True)
            messages.error(request, '❌ An unexpected error occurred. Please try again or email directly.')
    else:
        initial = {}
        service_slug = request.GET.get('service', '').strip()
        if service_slug:
            try:
                svc = Service.objects.get(slug=service_slug, is_active=True)
                initial['subject'] = f'Inquiry about {svc.title}'
                initial['message'] = f'Hi,\n\nI\'m interested in your {svc.title} service. '
            except Service.DoesNotExist:
                pass
        form = ContactForm(initial=initial)

    faqs = FAQ.objects.filter(is_active=True).order_by('order')[:8]
    response = render(request, 'core/contact.html', {
        'form': form,
        'site_settings': site_settings,
        'faqs': faqs,
    })
    response['X-Content-Type-Options'] = 'nosniff'
    response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# ─────────────────────────────────────────────
# Newsletter
# ─────────────────────────────────────────────

@require_POST
def newsletter_subscribe(request):
    try:
        if rate_limit_check(request, 'newsletter', limit=5, window_hours=24):
            return JsonResponse({'success': False, 'message': '⏳ Too many subscription attempts.'}, status=429)

        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data.get('name', '')

            existing = Newsletter.objects.filter(email=email).first()
            if existing:
                if existing.is_active and existing.is_verified:
                    return JsonResponse({'success': False, 'message': '📬 You\'re already on the list!'})
                newsletter = existing
                newsletter.is_active = True
                newsletter.name = name or newsletter.name
            else:
                newsletter = form.save(commit=False)
                newsletter.ip_address = get_client_ip(request)
                newsletter.source = request.GET.get('source', 'website')

            newsletter.verification_token = secrets.token_urlsafe(32)
            newsletter.save()

            try:
                today = timezone.now().date()
                snapshot, _ = AnalyticsSnapshot.objects.get_or_create(date=today)
                AnalyticsSnapshot.objects.filter(pk=snapshot.pk).update(
                    newsletter_signups=F('newsletter_signups') + 1
                )
            except Exception:
                pass

            try:
                site_settings = get_site_settings()
                verification_url = request.build_absolute_uri(
                    reverse('newsletter_verify', args=[newsletter.verification_token])
                )
                # Generate signed unsubscribe token
                signer = Signer()
                unsubscribe_token = signer.sign(newsletter.email)
                unsubscribe_url = request.build_absolute_uri(
                    reverse('newsletter_unsubscribe', args=[unsubscribe_token])
                )
                html = render_to_string('emails/newsletter_welcome.html', {
                    'newsletter': newsletter,
                    'site_settings': site_settings,
                    'verification_url': verification_url,
                    'unsubscribe_url': unsubscribe_url,
                })
                msg = EmailMultiAlternatives(
                    f"🎉 Welcome to the newsletter{', ' + name.split()[0] if name else ''}!",
                    strip_tags(html),
                    settings.DEFAULT_FROM_EMAIL,
                    [newsletter.email],
                )
                msg.attach_alternative(html, 'text/html')
                msg.send(fail_silently=True)
            except Exception as e:
                logger.warning(f"Newsletter email error: {e}")

            return JsonResponse({
                'success': True,
                'message': '🎉 Subscribed! Check your inbox to verify your email.'
            })
        else:
            return JsonResponse({'success': False, 'message': '❌ Please enter a valid email address.', 'errors': form.errors}, status=400)

    except Exception as e:
        logger.error(f"newsletter_subscribe error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': '❌ Something went wrong. Please try again.'}, status=500)


@require_GET
def newsletter_verify(request, token):
    try:
        newsletter = get_object_or_404(Newsletter, verification_token=token)
        newsletter.is_verified = True
        newsletter.is_active = True
        newsletter.verification_token = ''
        newsletter.save()
        messages.success(request, '✅ Email verified! Welcome to the newsletter.')
    except Exception as e:
        logger.error(f"newsletter_verify error: {e}")
        messages.error(request, '❌ This verification link is invalid or has already been used.')
    return redirect('home')


@require_GET
def newsletter_unsubscribe(request, token):
    """Unsubscribe using signed token instead of plain email."""
    signer = Signer()
    try:
        email = signer.unsign(token)
        newsletter = get_object_or_404(Newsletter, email=email)
        newsletter.is_active = False
        newsletter.unsubscribed_at = timezone.now()
        newsletter.save()
        return render(request, 'core/newsletter_unsubscribe.html', {
            'site_settings': get_site_settings(), 'success': True, 'email': email,
        })
    except BadSignature:
        logger.warning(f"Invalid unsubscribe token attempted")
    except Exception as e:
        logger.error(f"newsletter_unsubscribe error: {e}")
    return render(request, 'core/newsletter_unsubscribe.html', {
        'site_settings': get_site_settings(), 'success': False,
    })


@require_POST
def newsletter_feedback(request):
    """
    Optional: capture anonymous unsubscribe feedback.
    Stores reason in logs only to avoid collecting extra personal data.
    """
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        reason = str(data.get('reason', '')).strip()[:255]
        if reason:
            logger.info("Newsletter unsubscribe feedback: %s", reason)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"newsletter_feedback error: {e}", exc_info=True)
        return JsonResponse({'success': False}, status=400)


# ─────────────────────────────────────────────
# Services
# ─────────────────────────────────────────────

def services_view(request):
    try:
        site_settings = get_site_settings()
        services = Service.objects.filter(is_active=True).order_by('-featured', 'order')
        testimonials = Testimonial.objects.filter(is_approved=True, is_featured=True)[:6]
        faqs = FAQ.objects.filter(is_active=True).order_by('order')[:8]
        skills = Skill.objects.filter(is_active=True, featured=True).order_by('-proficiency')[:12]
        return render(request, 'core/services.html', {
            'services': services,
            'site_settings': site_settings,
            'testimonials': testimonials,
            'faqs': faqs,
            'skills': skills,
            'contact_form': ContactForm(),
        })
    except Exception as e:
        logger.error(f"services_view error: {e}", exc_info=True)
        return render(request, 'core/services.html', {
            'services': Service.objects.none(),
            'site_settings': get_site_settings(),
        })


def service_detail(request, slug):
    try:
        service = get_object_or_404(Service, slug=slug, is_active=True)
        site_settings = get_site_settings()
        related_services = (
            Service.objects.filter(is_active=True)
            .exclude(id=service.id)
            .order_by('-featured', '?')[:3]
        )
        testimonials = Testimonial.objects.filter(is_approved=True, is_featured=True)[:4]
        faqs = FAQ.objects.filter(is_active=True).order_by('order')[:6]
        initial = {
            'subject': f'Inquiry about {service.title}',
            'message': f'Hi,\n\nI\'m interested in your {service.title} service.\n\n',
        }
        contact_form = ContactForm(initial=initial)
        related_projects = Project.objects.filter(status='completed', featured=True).order_by('-views')[:3]
        return render(request, 'core/service_detail.html', {
            'service': service,
            'related_services': related_services,
            'testimonials': testimonials,
            'faqs': faqs,
            'site_settings': site_settings,
            'contact_form': contact_form,
            'related_projects': related_projects,
        })
    except Exception as e:
        logger.error(f"service_detail error: {e}", exc_info=True)
        messages.error(request, '❌ Service not found.')
        return redirect('services')


# ─────────────────────────────────────────────
# About
# ─────────────────────────────────────────────

def about_view(request):
    try:
        site_settings = get_site_settings()
        skills_qs = Skill.objects.filter(is_active=True).order_by('category', '-proficiency')
        grouped_skills = {}
        for skill in skills_qs:
            grouped_skills.setdefault(skill.get_category_display(), []).append(skill)
        return render(request, 'core/about.html', {
            'site_settings': site_settings,
            'skills': skills_qs,
            'skills_grouped': grouped_skills,
            'experiences': Experience.objects.all().order_by('-is_current', '-start_date'),
            'education': Education.objects.all().order_by('-is_current', '-start_date'),
            'certifications': Certification.objects.all().order_by('-issue_date'),
            'achievements': Achievement.objects.all().order_by('-date_achieved'),
            'social_proof': SocialProof.objects.filter(is_active=True).order_by('order'),
        })
    except Exception as e:
        logger.error(f"about_view error: {e}", exc_info=True)
        return render(request, 'core/about.html', {'site_settings': get_site_settings()})


# ─────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────

def search_view(request):
    query = request.GET.get('q', '').strip()
    context = {'query': query, 'site_settings': get_site_settings()}

    if len(query) >= 2:
        try:
            projects = Project.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(technologies__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(client__icontains=query),
                status='completed'
            ).distinct()[:10]

            posts = BlogPost.objects.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query),
                status='published'
            ).distinct()[:10]

            services = Service.objects.filter(
                Q(title__icontains=query) |
                Q(short_description__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            )[:5]

            context.update({
                'projects': projects,
                'posts': posts,
                'services': services,
                'total_results': projects.count() + posts.count() + services.count(),
            })
        except Exception as e:
            logger.error(f"search_view error: {e}")
            context.update({'projects': [], 'posts': [], 'services': [], 'total_results': 0})
    else:
        context.update({'projects': [], 'posts': [], 'services': [], 'total_results': 0})

    return render(request, 'core/search_results.html', context)


# ─────────────────────────────────────────────
# AJAX API Endpoints
# ─────────────────────────────────────────────

@require_POST
def project_like(request, slug):
    try:
        project = get_object_or_404(Project, slug=slug)
        liked = request.session.get('liked_projects', [])
        if project.id in liked:
            return JsonResponse({'success': False, 'message': 'Already liked', 'likes': project.likes, 'action': 'already_liked'})
        Project.objects.filter(pk=project.pk).update(likes=F('likes') + 1)
        project.refresh_from_db()
        liked.append(project.id)
        request.session['liked_projects'] = liked
        request.session.modified = True
        return JsonResponse({'success': True, 'likes': project.likes, 'action': 'liked', 'message': '❤️ Liked!'})
    except Exception as e:
        logger.error(f"project_like error: {e}")
        return JsonResponse({'success': False, 'message': '❌ Error'}, status=500)


@require_POST
def blog_like(request, slug):
    try:
        post = get_object_or_404(BlogPost, slug=slug, status='published')
        liked = request.session.get('liked_posts', [])
        if post.id in liked:
            return JsonResponse({'success': False, 'message': 'Already liked', 'likes': post.likes, 'action': 'already_liked'})
        BlogPost.objects.filter(pk=post.pk).update(likes=F('likes') + 1)
        post.refresh_from_db()
        liked.append(post.id)
        request.session['liked_posts'] = liked
        request.session.modified = True
        return JsonResponse({'success': True, 'likes': post.likes, 'action': 'liked', 'message': '❤️ Liked!'})
    except Exception as e:
        logger.error(f"blog_like error: {e}")
        return JsonResponse({'success': False, 'message': '❌ Error'}, status=500)


@require_GET
def api_projects(request):
    """JSON API endpoint: /api/projects/?category=&page=&search="""
    qs = Project.objects.filter(status='completed').select_related()
    category = request.GET.get('category', '')
    if category:
        qs = qs.filter(category=category)
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page', 1))
    data = {
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'results': [{
            'id': p.id, 'title': p.title, 'slug': p.slug,
            'category': p.category, 'description': p.description,
            'views': p.views, 'likes': p.likes,
            'url': request.build_absolute_uri(p.get_absolute_url()),
            'image': request.build_absolute_uri(p.featured_image.url) if p.featured_image else None,
            'tech_list': p.tech_list,
        } for p in page]
    }
    return JsonResponse(data)


# ─────────────────────────────────────────────
# Resume Download
# ─────────────────────────────────────────────

def download_resume(request):
    try:
        site_settings = get_site_settings()
        if site_settings and site_settings.resume_file:
            response = FileResponse(
                site_settings.resume_file.open('rb'),
                content_type='application/pdf'
            )
            name = (site_settings.site_name or 'Resume').replace(' ', '_')
            response['Content-Disposition'] = f'attachment; filename="{name}_Resume.pdf"'
            return response
        messages.warning(request, '📄 Resume not available at the moment. Please contact me directly.')
        return redirect('about')
    except Exception as e:
        logger.error(f"download_resume error: {e}")
        messages.error(request, '❌ Could not download resume. Please try again.')
        return redirect('about')


# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────

def error_404(request, exception):
    return render(request, 'errors/404.html', {'site_settings': get_site_settings()}, status=404)


def error_500(request):
    return render(request, 'errors/500.html', {'site_settings': get_site_settings()}, status=500)