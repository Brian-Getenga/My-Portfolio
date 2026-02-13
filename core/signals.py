from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from .models import ContactMessage, Newsletter, BlogPost, BlogComment, Project


@receiver(post_save, sender=ContactMessage)
def notify_admin_new_contact(sender, instance, created, **kwargs):
    """Send notification to admin when new contact message is received"""
    if created:
        try:
            from .models import SiteSettings
            site_settings = SiteSettings.load()
            
            # Prepare email context
            context = {
                'contact': instance,
                'site_settings': site_settings,
                'admin_url': f"{settings.SITE_URL}/admin/core/contactmessage/{instance.id}/change/" if hasattr(settings, 'SITE_URL') else '',
            }
            
            # Render HTML email
            html_content = render_to_string('emails/contact_admin_notification.html', context)
            text_content = f"""
New Contact Message Received

From: {instance.name}
Email: {instance.email}
Phone: {instance.phone or 'Not provided'}
Subject: {instance.subject}

Message:
{instance.message}

Budget: {instance.budget or 'Not specified'}
Timeline: {instance.timeline or 'Not specified'}
Priority: {instance.get_priority_display()}

Received: {instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}
IP Address: {instance.ip_address}
            """
            
            # Send email
            email = EmailMultiAlternatives(
                subject=f"🔔 New Contact: {instance.subject}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.ADMIN_EMAIL],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending contact notification: {e}")


@receiver(post_save, sender=Newsletter)
def welcome_newsletter_subscriber(sender, instance, created, **kwargs):
    """Send welcome email to new newsletter subscribers"""
    if created and not instance.is_verified:
        try:
            from .models import SiteSettings
            site_settings = SiteSettings.load()
            
            # Prepare email context
            context = {
                'newsletter': instance,
                'site_settings': site_settings,
                'verification_url': f"{settings.SITE_URL}/newsletter/verify/{instance.verification_token}/" if hasattr(settings, 'SITE_URL') else '',
                'unsubscribe_url': f"{settings.SITE_URL}/newsletter/unsubscribe/{instance.email}/" if hasattr(settings, 'SITE_URL') else '',
            }
            
            # Render HTML email
            html_content = render_to_string('emails/newsletter_welcome.html', context)
            text_content = f"""
Welcome to {site_settings.site_name} Newsletter!

Hi {instance.name or 'there'},

Thank you for subscribing to my newsletter! You'll receive updates about:

• New blog posts and technical articles
• Latest projects and case studies
• Web development tips and best practices
• Industry insights and trends
• Exclusive content for subscribers

Please verify your email address to activate your subscription:
{context.get('verification_url', 'Visit the website to verify')}

Looking forward to sharing valuable content with you!

Best regards,
{site_settings.site_name}

---
To unsubscribe: {context.get('unsubscribe_url', 'Visit the website')}
            """
            
            # Send email
            email = EmailMultiAlternatives(
                subject=f"Welcome to {site_settings.site_name} Newsletter! 🎉",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending welcome email: {e}")


@receiver(post_save, sender=BlogPost)
def notify_subscribers_new_post(sender, instance, created, **kwargs):
    """Notify newsletter subscribers when a new blog post is published"""
    # Only send if status changed from draft/scheduled to published
    if not created and instance.status == 'published':
        try:
            from .models import SiteSettings
            site_settings = SiteSettings.load()
            
            # Get active, verified subscribers
            subscribers = Newsletter.objects.filter(
                is_active=True,
                is_verified=True
            ).values_list('email', flat=True)
            
            if not subscribers:
                return
            
            # Prepare email context
            context = {
                'post': instance,
                'site_settings': site_settings,
                'post_url': f"{settings.SITE_URL}{instance.get_absolute_url()}" if hasattr(settings, 'SITE_URL') else '',
            }
            
            # Render HTML email
            html_content = render_to_string('emails/new_post_notification.html', context)
            text_content = f"""
New Article Published on {site_settings.site_name}

{instance.title}

{instance.excerpt}

Read the full article: {context.get('post_url', 'Visit the website')}

Reading time: {instance.reading_time} minutes

---
You're receiving this because you subscribed to {site_settings.site_name} newsletter.
            """
            
            # Send to subscribers in batches
            batch_size = 50
            for i in range(0, len(subscribers), batch_size):
                batch = subscribers[i:i+batch_size]
                
                email = EmailMultiAlternatives(
                    subject=f"📝 New Article: {instance.title}",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    bcc=list(batch),
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error notifying subscribers: {e}")


@receiver(post_save, sender=BlogComment)
def notify_admin_new_comment(sender, instance, created, **kwargs):
    """Notify admin of new blog comment"""
    if created and not instance.is_approved:
        try:
            from .models import SiteSettings
            site_settings = SiteSettings.load()
            
            context = {
                'comment': instance,
                'site_settings': site_settings,
                'post_url': f"{settings.SITE_URL}{instance.post.get_absolute_url()}" if hasattr(settings, 'SITE_URL') else '',
            }
            
            html_content = render_to_string('emails/comment_admin_notification.html', context)
            text_content = f"""
New Comment Pending Approval

Post: {instance.post.title}
Commenter: {instance.name} ({instance.email})

Comment:
{instance.content}

Approve or reject: {context.get('post_url', 'Check admin panel')}
            """
            
            email = EmailMultiAlternatives(
                subject=f"💬 New Comment on '{instance.post.title}'",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.ADMIN_EMAIL],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending comment notification: {e}")


@receiver(post_save, sender=BlogComment)
def notify_comment_reply(sender, instance, created, **kwargs):
    """Notify original commenter when someone replies"""
    if created and instance.parent and instance.is_approved:
        try:
            from .models import SiteSettings
            site_settings = SiteSettings.load()
            
            parent_comment = instance.parent
            
            context = {
                'comment': instance,
                'parent_comment': parent_comment,
                'site_settings': site_settings,
                'post_url': f"{settings.SITE_URL}{instance.post.get_absolute_url()}#comment-{instance.id}" if hasattr(settings, 'SITE_URL') else '',
            }
            
            html_content = render_to_string('emails/comment_reply_notification.html', context)
            text_content = f"""
Someone Replied to Your Comment

{instance.name} replied to your comment on "{instance.post.title}":

{instance.content}

View the conversation: {context.get('post_url', 'Visit the website')}
            """
            
            email = EmailMultiAlternatives(
                subject=f"💬 Reply to your comment on '{instance.post.title}'",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[parent_comment.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending reply notification: {e}")


@receiver(pre_save, sender=BlogPost)
def calculate_reading_time(sender, instance, **kwargs):
    """Auto-calculate reading time based on content"""
    if instance.content:
        # Strip HTML tags
        text = strip_tags(instance.content)
        # Count words
        word_count = len(text.split())
        # Average reading speed: 200 words per minute
        instance.reading_time = max(1, round(word_count / 200))


@receiver(post_save, sender=Project)
def notify_admin_project_milestone(sender, instance, created, **kwargs):
    """Notify admin when project reaches view milestone"""
    if not created:
        # Check for view milestones: 100, 500, 1000, 5000, 10000
        milestones = [100, 500, 1000, 5000, 10000]
        
        for milestone in milestones:
            if instance.views == milestone:
                try:
                    subject = f"🎉 Project Milestone: {instance.title} reached {milestone} views!"
                    message = f"""
Congratulations! Your project "{instance.title}" has reached {milestone} views.

Project Details:
- Category: {instance.get_category_display()}
- Status: {instance.get_status_display()}
- Total Likes: {instance.likes}
- Created: {instance.created_at.strftime('%Y-%m-%d')}

Keep up the great work!
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_EMAIL],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Error sending milestone notification: {e}")