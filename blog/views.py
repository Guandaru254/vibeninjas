from django.views.generic import ListView, DetailView
from .models import Post

class BlogListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'  # The file we will create next
    context_object_name = 'posts'         # The variable name used in the HTML loop
    
    def get_queryset(self):
        # Only show published posts, newest first
        return Post.objects.filter(is_published=True).order_by('-created_at')

class BlogDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug'  # Tells Django to look for 'slug' in the URL

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Increment view count every time someone reads
        obj.views += 1
        obj.save()
        return obj