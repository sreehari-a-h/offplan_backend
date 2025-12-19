# views.py
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.views.generic import ListView, DetailView

from api.models import BlogPost
from api.serializers import BlogPostSerializer
class BlogPostList(ListAPIView):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer

class BlogPostDetail(RetrieveAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

# Add these new views for SEO/crawlers
class BlogListView(ListView):
    model = BlogPost
    template_name = 'blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 10
    ordering = ['-created_at']

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'blog_detail.html'
    context_object_name = 'blog'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'