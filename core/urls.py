from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    
    # Projects
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('project/<slug:slug>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<slug:slug>/like/', views.project_like, name='project_like'),
    
    # Blog
    path('blog/', views.BlogListView.as_view(), name='blog'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('blog/<slug:slug>/like/', views.blog_like, name='blog_like'),
    path('blog/<slug:slug>/comment/', views.blog_comment_submit, name='blog_comment_submit'),
    
    # Services
    path('services/', views.services_view, name='services'),
    path('service/<slug:slug>/', views.service_detail, name='service_detail'),
    
    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/verify/<str:token>/', views.newsletter_verify, name='newsletter_verify'),
    path('newsletter/unsubscribe/<str:email>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    
    # Actions
    path('download-resume/', views.download_resume, name='download_resume'),
    path('search/', views.search_view, name='search'),
]