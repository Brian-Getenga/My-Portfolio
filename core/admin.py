"""
╔══════════════════════════════════════════════════════════════════╗
║         Brian Getenga Portfolio — Production Admin               ║
║         App Label : core                                         ║
║         Django    : 5.x   |   Python : 3.12                      ║
╚══════════════════════════════════════════════════════════════════╝
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.db.models import Count, Avg
import csv

from .models import (
    SiteSettings, Skill, Experience, Education, Certification,
    Project, ProjectGallery, BlogPost, BlogComment, Testimonial,
    ContactMessage, Newsletter, Achievement, Service, FAQ,
    SocialProof, AnalyticsSnapshot,
)

# ─────────────────────────────────────────────────────────────────
# Admin site meta
# ─────────────────────────────────────────────────────────────────
admin.site.site_header  = format_html(
    '<span style="font-family:\'Inter\',sans-serif;font-weight:800;'
    'letter-spacing:-0.5px;">Brian Getenga <span style="color:#6366f1;">Portfolio</span></span>'
)
admin.site.site_title   = "Portfolio Admin"
admin.site.index_title  = "🚀 Dashboard"

# ─────────────────────────────────────────────────────────────────
# Colour / badge helpers
# ─────────────────────────────────────────────────────────────────

def _badge(text, bg="#6b7280", fg="#fff"):
    """Render a pill-shaped badge."""
    return format_html(
        '<span style="background:{bg};color:{fg};padding:3px 10px;'
        'border-radius:20px;font-size:11px;font-weight:700;'
        'letter-spacing:.4px;white-space:nowrap;">{t}</span>',
        bg=bg, fg=fg, t=text,
    )


def _icon_badge(icon, text, bg="#6b7280"):
    return format_html(
        '<span style="background:{bg};color:#fff;padding:3px 10px;'
        'border-radius:20px;font-size:11px;font-weight:700;">{i} {t}</span>',
        bg=bg, i=icon, t=text,
    )


STATUS_PALETTE = {
    "published":   "#10b981",
    "draft":       "#f59e0b",
    "archived":    "#6b7280",
    "scheduled":   "#3b82f6",
    "completed":   "#059669",
    "in_progress": "#3b82f6",
    "planned":     "#8b5cf6",
    "low":         "#10b981",
    "medium":      "#f59e0b",
    "high":        "#ef4444",
    "urgent":      "#dc2626",
}

CATEGORY_COLORS = {
    "frontend":    "#3b82f6",
    "backend":     "#10b981",
    "database":    "#f59e0b",
    "devops":      "#8b5cf6",
    "mobile":      "#ec4899",
    "design":      "#14b8a6",
    "tools":       "#6366f1",
    "soft_skills": "#f97316",
    "other":       "#6b7280",
}

PROJECT_CAT_COLORS = {
    "web_app":    "#3b82f6",
    "mobile_app": "#10b981",
    "api":        "#f59e0b",
    "frontend":   "#8b5cf6",
    "fullstack":  "#ec4899",
    "design":     "#14b8a6",
    "other":      "#6b7280",
}

EMP_COLORS = {
    "full_time":  "#059669",
    "part_time":  "#3b82f6",
    "contract":   "#f59e0b",
    "freelance":  "#8b5cf6",
    "internship": "#6b7280",
}

PRIORITY_COLORS = {
    "low":    "#10b981",
    "medium": "#f59e0b",
    "high":   "#ef4444",
    "urgent": "#dc2626",
}

# ─────────────────────────────────────────────────────────────────
# Reusable Mixins
# ─────────────────────────────────────────────────────────────────

class ImagePreviewMixin:
    """Renders <img> thumbnails in list & change views."""

    def _img(self, url, w=60, h=60, radius=6):
        if url:
            return format_html(
                '<img src="{u}" style="width:{w}px;height:{h}px;'
                'object-fit:cover;border-radius:{r}px;'
                'border:2px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,.1);" />',
                u=url, w=w, h=h, r=radius,
            )
        return format_html(
            '<span style="display:inline-flex;align-items:center;justify-content:center;'
            'width:{w}px;height:{h}px;border-radius:{r}px;background:#f3f4f6;'
            'color:#9ca3af;font-size:10px;">None</span>',
            w=w, h=h, r=radius,
        )

    def image_preview(self, obj, field="image", w=60, h=60):
        img = getattr(obj, field, None)
        return self._img(img.url if img else None, w, h)
    image_preview.short_description = "Preview"

    def thumbnail_tag(self, obj):
        return self.image_preview(obj, "featured_image", 72, 54)
    thumbnail_tag.short_description = "Thumb"


class ExportCsvMixin:
    """Adds a CSV-export bulk action."""

    @admin.action(description="⬇ Export selected as CSV")
    def export_as_csv(self, request, queryset):
        meta   = self.model._meta
        fields = [f.name for f in meta.fields]
        resp   = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = (
            f'attachment; filename="{meta.verbose_name_plural}.csv"'
        )
        w = csv.writer(resp)
        w.writerow(fields)
        for obj in queryset:
            w.writerow([getattr(obj, f) for f in fields])
        return resp


# ─────────────────────────────────────────────────────────────────
# SiteSettings  (Singleton)
# ─────────────────────────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(ImagePreviewMixin, admin.ModelAdmin):

    list_display    = ("site_name", "_profile_preview", "email",
                       "location", "_avail", "maintenance_mode", "updated_at")
    readonly_fields = ("updated_at", "_profile_preview")

    fieldsets = (
        ("🌐 Basic Information", {
            "fields": (
                ("site_name", "tagline"),
                "site_description",
                "about_me",
                ("profile_image", "_profile_preview"),
                "resume_file",
            ),
        }),
        ("📞 Contact Details", {
            "fields": (("email", "phone"), ("location", "timezone")),
        }),
        ("🔗 Social Media Links", {
            "classes": ("collapse",),
            "fields": (
                ("github_url", "linkedin_url"),
                ("twitter_url", "instagram_url"),
                ("facebook_url", "youtube_url"),
                ("behance_url", "dribbble_url"),
            ),
        }),
        ("📊 Statistics", {
            "classes": ("collapse",),
            "fields": (
                ("years_experience", "projects_completed"),
                ("happy_clients",    "coffee_consumed"),
                "code_commits",
            ),
        }),
        ("🔍 SEO & Analytics", {
            "classes": ("collapse",),
            "fields": (
                "meta_keywords",
                "meta_description",
                ("google_analytics_id", "google_site_verification"),
                "facebook_pixel_id",
            ),
        }),
        ("⚙️ Features & Availability", {
            "fields": (
                ("enable_blog", "enable_newsletter", "enable_testimonials"),
                ("enable_dark_mode", "maintenance_mode"),
                ("available_for_work", "available_for_freelance"),
                "hourly_rate",
            ),
        }),
        ("📝 Footer", {"fields": ("footer_text",)}),
    )

    # ── helpers ──────────────────────────────────────────────────
    def _profile_preview(self, obj):
        return self.image_preview(obj, "profile_image", 90, 90)
    _profile_preview.short_description = "Profile Photo"

    def _avail(self, obj):
        if obj.available_for_work:
            return _icon_badge("✅", "Available", "#059669")
        return _icon_badge("🔴", "Unavailable", "#ef4444")
    _avail.short_description = "Availability"

    # ── singleton guards ─────────────────────────────────────────
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Always redirect list → the single change form."""
        obj = SiteSettings.load()
        # ✅ Fixed: app label is 'core', not 'portfolio'
        return HttpResponseRedirect(
            reverse("admin:core_sitesettings_change", args=[obj.pk])
        )


# ─────────────────────────────────────────────────────────────────
# Skill
# ─────────────────────────────────────────────────────────────────

@admin.register(Skill)
class SkillAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("name", "_cat_badge", "_proficiency_bar",
                      "years_experience", "featured", "is_active", "order")
    list_filter    = ("category", "is_active", "featured")
    search_fields  = ("name", "description")
    list_editable  = ("order", "is_active", "featured")
    ordering       = ("-featured", "order", "name")
    actions        = ["export_as_csv", "activate", "deactivate", "mark_featured"]

    fieldsets = (
        ("Skill Details", {
            "fields": (
                ("name", "category"),
                ("proficiency", "years_experience"),
                "description",
            ),
        }),
        ("Display Settings", {
            "fields": (
                ("icon_class", "icon_image"),
                ("order", "featured", "is_active"),
            ),
        }),
    )

    def _cat_badge(self, obj):
        return _badge(obj.get_category_display(),
                      CATEGORY_COLORS.get(obj.category, "#6b7280"))
    _cat_badge.short_description = "Category"
    _cat_badge.admin_order_field = "category"

    def _proficiency_bar(self, obj):
        p = obj.proficiency
        c = "#10b981" if p >= 75 else "#f59e0b" if p >= 50 else "#ef4444"
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:100px;background:#e5e7eb;border-radius:99px;height:10px;'
            'overflow:hidden;">'
            '<div style="width:{p}%;background:{c};height:10px;border-radius:99px;'
            'transition:width .3s;"></div></div>'
            '<span style="font-size:11px;font-weight:700;color:#374151;">{p}%</span>'
            '</div>',
            p=p, c=c,
        )
    _proficiency_bar.short_description = "Proficiency"

    @admin.action(description="✅ Activate selected")
    def activate(self, request, qs):
        n = qs.update(is_active=True)
        self.message_user(request, f"{n} skill(s) activated.", messages.SUCCESS)

    @admin.action(description="🚫 Deactivate selected")
    def deactivate(self, request, qs):
        n = qs.update(is_active=False)
        self.message_user(request, f"{n} skill(s) deactivated.", messages.WARNING)

    @admin.action(description="⭐ Mark as Featured")
    def mark_featured(self, request, qs):
        n = qs.update(featured=True)
        self.message_user(request, f"{n} skill(s) featured.", messages.SUCCESS)


# ─────────────────────────────────────────────────────────────────
# Experience
# ─────────────────────────────────────────────────────────────────

@admin.register(Experience)
class ExperienceAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("title", "company", "_emp_badge", "start_date",
                      "_end", "_dur", "is_current", "order")
    list_filter    = ("employment_type", "is_current")
    search_fields  = ("title", "company", "technologies")
    list_editable  = ("order", "is_current")
    date_hierarchy = "start_date"
    actions        = ["export_as_csv"]

    fieldsets = (
        ("💼 Position", {
            "fields": (
                ("title", "employment_type"),
                ("company", "company_url"),
                "company_logo",
                "location",
            ),
        }),
        ("📅 Timeline", {
            "fields": (("start_date", "end_date"), "is_current"),
        }),
        ("📄 Details", {
            "fields": ("description", "achievements", "technologies", "order"),
        }),
    )

    def _emp_badge(self, obj):
        return _badge(obj.get_employment_type_display(),
                      EMP_COLORS.get(obj.employment_type, "#6b7280"))
    _emp_badge.short_description = "Type"

    def _end(self, obj):
        if obj.is_current:
            return format_html(
                '<span style="color:#059669;font-weight:700;">▶ Present</span>'
            )
        return obj.end_date or "—"
    _end.short_description = "End Date"

    def _dur(self, obj):
        return format_html(
            '<span style="color:#6b7280;font-size:12px;white-space:nowrap;">🕐 {}</span>',
            obj.duration,
        )
    _dur.short_description = "Duration"


# ─────────────────────────────────────────────────────────────────
# Education
# ─────────────────────────────────────────────────────────────────

@admin.register(Education)
class EducationAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display   = ("degree", "field_of_study", "institution",
                      "start_date", "end_date", "_grade_badge", "is_current", "order")
    list_filter    = ("is_current",)
    search_fields  = ("degree", "field_of_study", "institution")
    list_editable  = ("order", "is_current")
    actions        = ["export_as_csv"]

    def _grade_badge(self, obj):
        if obj.grade:
            return _badge(obj.grade, "#6366f1")
        return "—"
    _grade_badge.short_description = "Grade"


# ─────────────────────────────────────────────────────────────────
# Certification
# ─────────────────────────────────────────────────────────────────

@admin.register(Certification)
class CertificationAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display      = ("name", "issuing_organization", "issue_date",
                         "_expiry", "_valid_badge", "_cert_thumb", "order")
    list_filter       = ("issuing_organization",)
    search_fields     = ("name", "issuing_organization", "credential_id")
    filter_horizontal = ("skills",)
    readonly_fields   = ("_cert_thumb",)
    actions           = ["export_as_csv"]

    def _cert_thumb(self, obj):
        return self.image_preview(obj, "certificate_image", 100, 75)
    _cert_thumb.short_description = "Certificate"

    def _expiry(self, obj):
        return obj.expiry_date or format_html(
            '<span style="color:#059669;font-weight:600;">♾ No Expiry</span>'
        )
    _expiry.short_description = "Expires"

    def _valid_badge(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="color:#ef4444;font-weight:700;">⚠ Expired</span>'
            )
        return format_html(
            '<span style="color:#059669;font-weight:700;">✓ Valid</span>'
        )
    _valid_badge.short_description = "Status"


# ─────────────────────────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────────────────────────

class ProjectGalleryInline(admin.TabularInline):
    model           = ProjectGallery
    extra           = 2
    fields          = ("image", "_prev", "caption", "order")
    readonly_fields = ("_prev",)

    def _prev(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width:90px;height:65px;'
                'object-fit:cover;border-radius:5px;'
                'border:1px solid #e5e7eb;" />',
                obj.image.url,
            )
        return "—"
    _prev.short_description = "Preview"


@admin.register(Project)
class ProjectAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("thumbnail_tag", "title", "_cat_badge", "_status_badge",
                      "_tech_pills", "_views_pill", "featured", "order", "created_at")
    list_filter    = ("status", "category", "featured")
    search_fields  = ("title", "description", "technologies", "client")
    list_editable  = ("featured", "order")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "likes", "created_at", "updated_at", "thumbnail_tag")
    date_hierarchy  = "project_date"
    inlines         = [ProjectGalleryInline]
    actions         = ["export_as_csv", "mark_featured", "mark_completed",
                       "mark_in_progress", "reset_views"]

    fieldsets = (
        ("📋 Basic Information", {
            "fields": (
                ("title", "slug"),
                ("category", "status"),
                "description",
                "full_description",
            ),
        }),
        ("🖼️ Media", {
            "fields": (("featured_image", "thumbnail_tag"),),
        }),
        ("🔗 Links & Details", {
            "fields": (
                ("github_url", "live_url"),
                "video_url",
                ("client", "client_url"),
                ("project_date", "duration"),
                ("team_size", "role"),
                "technologies",
            ),
        }),
        ("⚙️ Meta & Settings", {
            "fields": (
                ("featured", "order"),
                ("views", "likes"),
                "meta_description",
            ),
        }),
        ("🕒 Timestamps", {
            "classes": ("collapse",),
            "fields": (("created_at", "updated_at"),),
        }),
    )

    def _cat_badge(self, obj):
        return _badge(obj.get_category_display(),
                      PROJECT_CAT_COLORS.get(obj.category, "#6b7280"))
    _cat_badge.short_description = "Category"

    def _status_badge(self, obj):
        return _badge(
            obj.get_status_display(),
            STATUS_PALETTE.get(obj.status, "#6b7280"),
        )
    _status_badge.short_description = "Status"
    _status_badge.admin_order_field = "status"

    def _tech_pills(self, obj):
        techs = obj.tech_list
        html  = "".join(
            f'<span style="background:#ede9fe;color:#5b21b6;padding:1px 7px;'
            f'border-radius:99px;font-size:10px;margin:1px;display:inline-block;">{t}</span>'
            for t in techs[:3]
        )
        if len(techs) > 3:
            html += (
                f'<span style="color:#9ca3af;font-size:10px;"> +{len(techs)-3}</span>'
            )
        return format_html(html) if html else "—"
    _tech_pills.short_description = "Technologies"

    def _views_pill(self, obj):
        return format_html(
            '<span style="background:#eff6ff;color:#1d4ed8;padding:2px 8px;'
            'border-radius:99px;font-size:11px;font-weight:700;">👁 {}</span>',
            obj.views,
        )
    _views_pill.short_description = "Views"
    _views_pill.admin_order_field = "views"

    @admin.action(description="⭐ Mark as Featured")
    def mark_featured(self, request, qs):
        n = qs.update(featured=True)
        self.message_user(request, f"{n} project(s) featured.", messages.SUCCESS)

    @admin.action(description="✅ Mark as Completed")
    def mark_completed(self, request, qs):
        n = qs.update(status="completed")
        self.message_user(request, f"{n} project(s) marked completed.", messages.SUCCESS)

    @admin.action(description="🔵 Mark as In Progress")
    def mark_in_progress(self, request, qs):
        n = qs.update(status="in_progress")
        self.message_user(request, f"{n} project(s) set to In Progress.", messages.SUCCESS)

    @admin.action(description="🔄 Reset view counts to 0")
    def reset_views(self, request, qs):
        n = qs.update(views=0)
        self.message_user(request, f"Views reset for {n} project(s).", messages.WARNING)


# ─────────────────────────────────────────────────────────────────
# ProjectGallery  (standalone bulk management)
# ─────────────────────────────────────────────────────────────────

@admin.register(ProjectGallery)
class ProjectGalleryAdmin(admin.ModelAdmin):
    list_display  = ("_thumb", "project", "caption", "order")
    list_filter   = ("project",)
    search_fields = ("project__title", "caption")
    list_editable = ("order",)

    def _thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:80px;height:56px;'
                'object-fit:cover;border-radius:5px;border:1px solid #e5e7eb;" />',
                obj.image.url,
            )
        return "—"
    _thumb.short_description = "Image"


# ─────────────────────────────────────────────────────────────────
# BlogPost
# ─────────────────────────────────────────────────────────────────

class BlogCommentInline(admin.TabularInline):
    model            = BlogComment
    extra            = 0
    fields           = ("name", "email", "content", "is_approved", "created_at")
    readonly_fields  = ("name", "email", "content", "created_at")
    can_delete       = True
    show_change_link = True
    verbose_name_plural = "Comments on this post"


@admin.register(BlogPost)
class BlogPostAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("thumbnail_tag", "title", "author", "_status_badge",
                      "published_date", "_read_time", "_views_pill",
                      "_comments_count", "featured")
    list_filter    = ("status", "featured", "author")
    search_fields  = ("title", "excerpt", "content")
    list_editable  = ("featured",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "likes", "reading_time", "created_at",
                       "updated_at", "published_date", "thumbnail_tag")
    date_hierarchy  = "published_date"
    inlines         = [BlogCommentInline]
    actions         = ["export_as_csv", "publish_posts", "draft_posts", "mark_featured"]

    fieldsets = (
        ("📝 Content", {
            "fields": (
                ("title", "slug"),
                "excerpt",
                "content",
                ("featured_image", "thumbnail_tag"),
            ),
        }),
        ("⚙️ Publishing", {
            "fields": (
                ("status", "author"),
                ("published_date", "scheduled_date"),
                ("featured", "allow_comments"),
            ),
        }),
        ("🔍 SEO", {
            "classes": ("collapse",),
            "fields": ("meta_description", "canonical_url", "tags"),
        }),
        ("📊 Stats (read-only)", {
            "classes": ("collapse",),
            "fields": (("views", "likes", "reading_time"), ("created_at", "updated_at")),
        }),
    )

    def _status_badge(self, obj):
        return _badge(
            obj.get_status_display(),
            STATUS_PALETTE.get(obj.status, "#6b7280"),
        )
    _status_badge.short_description = "Status"
    _status_badge.admin_order_field = "status"

    def _read_time(self, obj):
        return format_html(
            '<span style="color:#6b7280;font-size:12px;">⏱ {} min</span>',
            obj.reading_time,
        )
    _read_time.short_description = "Read Time"

    def _views_pill(self, obj):
        return format_html(
            '<span style="background:#eff6ff;color:#1d4ed8;padding:2px 8px;'
            'border-radius:99px;font-size:11px;font-weight:700;">👁 {}</span>',
            obj.views,
        )
    _views_pill.short_description = "Views"
    _views_pill.admin_order_field = "views"

    def _comments_count(self, obj):
        total   = obj.comments.count()
        pending = obj.comments.filter(is_approved=False).count()
        if pending:
            return format_html(
                '💬 {} <span style="color:#ef4444;font-size:10px;font-weight:700;">'
                '({}⚠)</span>',
                total, pending,
            )
        return format_html("💬 {}", total)
    _comments_count.short_description = "Comments"

    @admin.action(description="🚀 Publish selected posts")
    def publish_posts(self, request, qs):
        n = qs.filter(status__in=["draft", "scheduled"]).update(
            status="published", published_date=timezone.now()
        )
        self.message_user(request, f"{n} post(s) published.", messages.SUCCESS)

    @admin.action(description="📝 Move selected to Draft")
    def draft_posts(self, request, qs):
        n = qs.update(status="draft")
        self.message_user(request, f"{n} post(s) moved to draft.", messages.WARNING)

    @admin.action(description="⭐ Mark selected as Featured")
    def mark_featured(self, request, qs):
        n = qs.update(featured=True)
        self.message_user(request, f"{n} post(s) featured.", messages.SUCCESS)


# ─────────────────────────────────────────────────────────────────
# BlogComment
# ─────────────────────────────────────────────────────────────────

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):

    list_display   = ("name", "email", "_post_link", "_approval_badge",
                      "_type", "created_at")
    list_filter    = ("is_approved", "created_at")
    search_fields  = ("name", "email", "content", "post__title")
    readonly_fields = ("ip_address", "created_at", "updated_at")
    actions = ["approve_comments", "unapprove_comments"]

    def _post_link(self, obj):
        # ✅ Fixed: use 'core' app label
        url = reverse("admin:core_blogpost_change", args=[obj.post.pk])
        return format_html('<a href="{}">{}</a>', url, obj.post.title[:45])
    _post_link.short_description = "Post"

    def _approval_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="color:#059669;font-weight:700;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color:#ef4444;font-weight:700;">✗ Pending</span>'
        )
    _approval_badge.short_description = "Status"
    _approval_badge.admin_order_field = "is_approved"

    def _type(self, obj):
        return format_html(
            '<span style="color:#8b5cf6;">↩ Reply</span>'
        ) if obj.parent else format_html(
            '<span style="color:#6b7280;">● Root</span>'
        )
    _type.short_description = "Type"

    @admin.action(description="✅ Approve selected comments")
    def approve_comments(self, request, qs):
        n = qs.update(is_approved=True)
        self.message_user(request, f"{n} comment(s) approved.", messages.SUCCESS)

    @admin.action(description="🚫 Unapprove selected comments")
    def unapprove_comments(self, request, qs):
        n = qs.update(is_approved=False)
        self.message_user(request, f"{n} comment(s) unapproved.", messages.WARNING)


# ─────────────────────────────────────────────────────────────────
# Testimonial
# ─────────────────────────────────────────────────────────────────

@admin.register(Testimonial)
class TestimonialAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("_photo", "name", "position", "company",
                      "_stars", "_project_link", "is_featured", "is_approved", "order")
    list_filter    = ("is_featured", "is_approved", "rating")
    search_fields  = ("name", "company", "content")
    list_editable  = ("is_featured", "is_approved", "order")
    readonly_fields = ("_photo",)
    actions = ["export_as_csv", "approve_all", "feature_all"]

    def _photo(self, obj):
        return self.image_preview(obj, "image", 52, 52)
    _photo.short_description = "Photo"

    def _stars(self, obj):
        filled = "★" * obj.rating
        empty  = "☆" * (5 - obj.rating)
        color  = "#f59e0b" if obj.rating >= 4 else "#9ca3af"
        return format_html(
            '<span style="color:{c};font-size:15px;">{f}</span>'
            '<span style="color:#d1d5db;font-size:15px;">{e}</span>',
            c=color, f=filled, e=empty,
        )
    _stars.short_description = "Rating"
    _stars.admin_order_field = "rating"

    def _project_link(self, obj):
        if obj.project:
            # ✅ Fixed: use 'core' app label
            url = reverse("admin:core_project_change", args=[obj.project.pk])
            return format_html('<a href="{}">{}</a>', url, obj.project.title[:30])
        return "—"
    _project_link.short_description = "Project"

    @admin.action(description="✅ Approve selected")
    def approve_all(self, request, qs):
        n = qs.update(is_approved=True)
        self.message_user(request, f"{n} testimonial(s) approved.", messages.SUCCESS)

    @admin.action(description="⭐ Feature selected")
    def feature_all(self, request, qs):
        n = qs.update(is_featured=True)
        self.message_user(request, f"{n} testimonial(s) featured.", messages.SUCCESS)


# ─────────────────────────────────────────────────────────────────
# ContactMessage
# ─────────────────────────────────────────────────────────────────

@admin.register(ContactMessage)
class ContactMessageAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("name", "email", "_subj", "_priority_badge",
                      "_read_status", "_responded_status", "created_at")
    list_filter    = ("is_read", "is_responded", "priority", "created_at")
    search_fields  = ("name", "email", "subject", "message")
    readonly_fields = ("ip_address", "user_agent", "referrer",
                       "created_at", "updated_at")
    date_hierarchy = "created_at"
    actions = ["export_as_csv", "mark_read", "mark_unread", "mark_responded"]

    fieldsets = (
        ("👤 Sender", {"fields": (("name", "email"), "phone")}),
        ("✉️ Message", {"fields": ("subject", "message", ("budget", "timeline"))}),
        ("⚙️ Status", {
            "fields": (("priority", "is_read", "is_responded"), "response_date"),
        }),
        ("🔒 Technical Meta", {
            "classes": ("collapse",),
            "fields": ("ip_address", "user_agent", "referrer", "created_at", "updated_at"),
        }),
    )

    def _subj(self, obj):
        s = obj.subject
        return (s[:52] + "…") if len(s) > 52 else s
    _subj.short_description = "Subject"

    def _priority_badge(self, obj):
        return _badge(obj.get_priority_display(),
                      PRIORITY_COLORS.get(obj.priority, "#6b7280"))
    _priority_badge.short_description = "Priority"
    _priority_badge.admin_order_field = "priority"

    def _read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#059669;">✓ Read</span>')
        return format_html(
            '<span style="color:#ef4444;font-weight:700;'
            'animation:blink 1s step-start infinite;">● Unread</span>'
        )
    _read_status.short_description = "Read"
    _read_status.admin_order_field = "is_read"

    def _responded_status(self, obj):
        if obj.is_responded:
            return format_html('<span style="color:#059669;">✓ Responded</span>')
        return format_html('<span style="color:#f59e0b;">⏳ Pending</span>')
    _responded_status.short_description = "Response"
    _responded_status.admin_order_field = "is_responded"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Auto-mark as read when an admin opens the message."""
        ContactMessage.objects.filter(pk=object_id, is_read=False).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description="📬 Mark selected as Read")
    def mark_read(self, request, qs):
        n = qs.update(is_read=True)
        self.message_user(request, f"{n} message(s) marked as read.", messages.SUCCESS)

    @admin.action(description="📭 Mark selected as Unread")
    def mark_unread(self, request, qs):
        n = qs.update(is_read=False)
        self.message_user(request, f"{n} message(s) marked as unread.", messages.INFO)

    @admin.action(description="✅ Mark selected as Responded")
    def mark_responded(self, request, qs):
        n = qs.update(is_responded=True, response_date=timezone.now())
        self.message_user(request, f"{n} message(s) marked as responded.", messages.SUCCESS)


# ─────────────────────────────────────────────────────────────────
# Newsletter
# ─────────────────────────────────────────────────────────────────

@admin.register(Newsletter)
class NewsletterAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("email", "name", "_active_badge", "_verified_badge",
                      "source", "subscribed_at")
    list_filter    = ("is_active", "is_verified", "source")
    search_fields  = ("email", "name")
    readonly_fields = ("subscribed_at", "verification_token", "ip_address")
    date_hierarchy = "subscribed_at"
    actions = ["export_as_csv", "activate_subs", "deactivate_subs"]

    def _active_badge(self, obj):
        return _badge("Active", "#059669") if obj.is_active else _badge("Inactive", "#6b7280")
    _active_badge.short_description = "Active"
    _active_badge.admin_order_field = "is_active"

    def _verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#059669;font-weight:700;">✓ Verified</span>')
        return format_html('<span style="color:#f59e0b;">⏳ Unverified</span>')
    _verified_badge.short_description = "Verified"

    @admin.action(description="✅ Activate selected subscriptions")
    def activate_subs(self, request, qs):
        n = qs.update(is_active=True)
        self.message_user(request, f"{n} subscription(s) activated.", messages.SUCCESS)

    @admin.action(description="🚫 Deactivate selected subscriptions")
    def deactivate_subs(self, request, qs):
        n = qs.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f"{n} subscription(s) deactivated.", messages.WARNING)


# ─────────────────────────────────────────────────────────────────
# Achievement
# ─────────────────────────────────────────────────────────────────

ACH_COLORS = {
    "award":         "#f59e0b",
    "certification": "#3b82f6",
    "milestone":     "#059669",
    "recognition":   "#8b5cf6",
    "publication":   "#ec4899",
}


@admin.register(Achievement)
class AchievementAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("title", "_cat_badge", "issuer", "date_achieved",
                      "_img_preview", "order")
    list_filter    = ("category",)
    search_fields  = ("title", "issuer", "description")
    list_editable  = ("order",)
    readonly_fields = ("_img_preview",)
    actions = ["export_as_csv"]

    def _cat_badge(self, obj):
        return _badge(obj.get_category_display(),
                      ACH_COLORS.get(obj.category, "#6b7280"))
    _cat_badge.short_description = "Category"

    def _img_preview(self, obj):
        return self.image_preview(obj, "image", 64, 64)
    _img_preview.short_description = "Image"


# ─────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────

@admin.register(Service)
class ServiceAdmin(ImagePreviewMixin, ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("_svc_thumb", "title", "_price_badge",
                      "is_active", "featured", "order")
    list_filter    = ("is_active", "featured")
    search_fields  = ("title", "short_description")
    list_editable  = ("is_active", "featured", "order")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("_svc_thumb",)
    actions = ["export_as_csv", "activate_svcs", "deactivate_svcs"]

    fieldsets = (
        ("🛠 Service Info", {
            "fields": (
                ("title", "slug"),
                ("icon", "image", "_svc_thumb"),
                "short_description",
                "description",
            ),
        }),
        ("💵 Pricing & Process", {
            "fields": ("starting_price", "deliverables", "process_steps"),
        }),
        ("⚙️ Settings", {
            "fields": (("order", "is_active", "featured"),),
        }),
    )

    def _svc_thumb(self, obj):
        return self.image_preview(obj, "image", 64, 64)
    _svc_thumb.short_description = "Preview"

    def _price_badge(self, obj):
        if obj.starting_price:
            return format_html(
                '<span style="background:#d1fae5;color:#065f46;padding:3px 10px;'
                'border-radius:99px;font-size:11px;font-weight:700;">From ${}</span>',
                obj.starting_price,
            )
        return format_html('<span style="color:#9ca3af;font-size:12px;">TBD</span>')
    _price_badge.short_description = "Price"
    _price_badge.admin_order_field = "starting_price"

    @admin.action(description="✅ Activate selected services")
    def activate_svcs(self, request, qs):
        n = qs.update(is_active=True)
        self.message_user(request, f"{n} service(s) activated.", messages.SUCCESS)

    @admin.action(description="🚫 Deactivate selected services")
    def deactivate_svcs(self, request, qs):
        n = qs.update(is_active=False)
        self.message_user(request, f"{n} service(s) deactivated.", messages.WARNING)


# ─────────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────────

@admin.register(FAQ)
class FAQAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("_q", "_cat_badge", "order", "is_active")
    list_filter    = ("is_active", "category")
    search_fields  = ("question", "category")
    list_editable  = ("order", "is_active")
    actions        = ["export_as_csv"]

    def _q(self, obj):
        return (obj.question[:80] + "…") if len(obj.question) > 80 else obj.question
    _q.short_description = "Question"

    def _cat_badge(self, obj):
        if obj.category:
            return _badge(obj.category, "#6366f1")
        return "—"
    _cat_badge.short_description = "Category"


# ─────────────────────────────────────────────────────────────────
# SocialProof
# ─────────────────────────────────────────────────────────────────

SP_COLORS = {
    "clients":    "#059669",
    "projects":   "#3b82f6",
    "experience": "#8b5cf6",
    "rating":     "#f59e0b",
    "response":   "#ec4899",
    "custom":     "#6b7280",
}


@admin.register(SocialProof)
class SocialProofAdmin(ExportCsvMixin, admin.ModelAdmin):

    list_display   = ("label", "_mtype_badge", "_value_display", "order", "is_active")
    list_filter    = ("metric_type", "is_active")
    search_fields  = ("label", "value")
    list_editable  = ("order", "is_active")
    actions        = ["export_as_csv"]

    def _mtype_badge(self, obj):
        return _badge(obj.get_metric_type_display(),
                      SP_COLORS.get(obj.metric_type, "#6b7280"))
    _mtype_badge.short_description = "Type"

    def _value_display(self, obj):
        return format_html(
            '<span style="font-size:16px;font-weight:800;color:#111827;">{}</span>',
            obj.value,
        )
    _value_display.short_description = "Value"


# ─────────────────────────────────────────────────────────────────
# AnalyticsSnapshot  (read-only)
# ─────────────────────────────────────────────────────────────────

@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):

    list_display   = ("date", "_pv", "_uv", "_bv", "_prv",
                      "contact_submissions", "newsletter_signups")
    readonly_fields = ("date", "page_views", "unique_visitors",
                       "blog_views", "project_views",
                       "contact_submissions", "newsletter_signups")
    date_hierarchy = "date"

    def _stat(self, val, color="#3b82f6"):
        return format_html(
            '<span style="font-weight:700;color:{};">{}</span>', color, val
        )

    def _pv(self, obj):  return self._stat(obj.page_views, "#3b82f6")
    def _uv(self, obj):  return self._stat(obj.unique_visitors, "#059669")
    def _bv(self, obj):  return self._stat(obj.blog_views, "#8b5cf6")
    def _prv(self, obj): return self._stat(obj.project_views, "#f59e0b")

    _pv.short_description  = "Page Views"
    _uv.short_description  = "Unique Visitors"
    _bv.short_description  = "Blog Views"
    _prv.short_description = "Project Views"

    _pv.admin_order_field  = "page_views"
    _uv.admin_order_field  = "unique_visitors"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser