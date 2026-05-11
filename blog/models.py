from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    # Make icon optional with blank=True
    icon = models.CharField(max_length=10, default="🔥", blank=True) 
    description = models.TextField(blank=True, help_text="Category description (optional)")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def get_absolute_url(self):
        """URL for category page (if you add category filtering later)"""
        return f"/blog/?category={self.slug}"

class Post(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    
    # Pointing to the custom user model defined in your settings
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='posts'
    )
    
    # Content - Summernote will turn this into a world-class editor
    content = models.TextField() 
    featured_image = models.ImageField(
        upload_to='blog_images/%Y/%m/',
        blank=True,
        null=True,
        help_text="Recommended size: 1200x675px (16:9 ratio)"
    )
    
    # SEO & Stats
    meta_description = models.CharField(
        max_length=160, 
        blank=True,
        help_text="Search engine summary (Best for SEO, 120-160 chars)"
    )
    views = models.PositiveIntegerField(default=0, editable=False)
    is_published = models.BooleanField(
        default=False,
        help_text="Check to make this post visible on the website"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Canonical URL for this post"""
        return reverse('blog:detail', kwargs={'slug': self.slug})
    
    def get_reading_time(self):
        """Estimate reading time (200 words per minute)"""
        word_count = len(self.content.split())
        minutes = word_count / 200
        return max(1, round(minutes))  # Minimum 1 minute

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"