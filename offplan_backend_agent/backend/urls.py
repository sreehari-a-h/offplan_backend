"""
URL configuration for backend project.
"""
from django.contrib import admin
from api.views import AgentListView
from django.urls import path, include
from api.staticpagessitemap import StaticPagesSitemap
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views.agent_details_username import AgentDetailByUsernameView
from django.http import HttpResponse
from api.views.property_filter import FilterPropertiesView
from api.views.properties_list import PropertyListView
from api.views.property_details import PropertyDetailView
from api.views.cities_list import CityListView
from api.views.agent_register import AgentRegisterView
from api.views.agent_update import AgentUpdateView
from api.views.agent_delete import AgentDeleteView
from api.views.property_status_counts import PropertyStatusCountView
from api.views.property_city_count import PropertyByStatusView
from api.views.consultation import ConsultationView
from api.views.subscription import SubscribeView
from api.views.developers_list import DeveloperListView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from api.views.meta_view import agent_meta_view
from django.contrib.sitemaps.views import sitemap
from api.agentsitemap import AgentDetailsSitemap
from api.blogsitemap import BlogPostSitemap
from api.homepagesitemap import HomePageSitemap
from api.views.meta_view import (
    agent_meta_view,
    blogs_listing_meta_view,
    blog_detail_meta_view,
    contact_meta_view,
    about_meta_view,
)


schema_view = get_schema_view(
   openapi.Info(
      title="Offplan Agent API",
      default_version='v1',
      description="API documentation for agent listing and admin operations",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
   authentication_classes=[],
)

sitemaps_dict = {
    'home': HomePageSitemap,
    'blogs': BlogPostSitemap,
    'agents': AgentDetailsSitemap,
    'static': StaticPagesSitemap,
}

urlpatterns = [
    path('', lambda request: HttpResponse("🚀 Offplan Backend is running!")),
    path('admin/', admin.site.urls),

    # CRITICAL: Sitemap MUST come before catch-all patterns
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict}, name="django.contrib.sitemaps.views.sitemap"),
    
    # Other specific routes
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # SEO meta prerender routes (specific paths before catch-all)
    path('blogs/', blogs_listing_meta_view, name="blogs-listing-meta"),
    path('blog/<slug:slug>/', blog_detail_meta_view, name="blog-detail-meta"),
    path('<str:username>/contact/', contact_meta_view, name="contact-meta"),
    path('<str:username>/about/', about_meta_view, name="about-meta"),
    
    # Catch-all patterns MUST be at the end
    # Use negative lookahead to exclude 'sitemap' from username pattern
    re_path(r'^(?!sitemap)(?P<username>[a-zA-Z0-9_-]+)/?$', agent_meta_view, name="agent-meta"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)