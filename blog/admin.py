from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Post, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug', 'post_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name',)
    
    def post_count(self, obj):
        """Show number of posts in this category"""
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):
    # Enables the "World-Class" Summernote editor for the content field
    summernote_fields = ('content',) 
    
    list_display = ('title', 'author', 'category', 'is_published', 'featured_badge', 'views', 'created_at')
    list_filter = ('is_published', 'category', 'created_at', 'author')
    search_fields = ('title', 'content', 'meta_description')
    list_editable = ('is_published',)  # Quick publish/unpublish from list view
    date_hierarchy = 'created_at'  # Add date navigation
    
    # Automatically fills the slug as you type the title
    prepopulated_fields = {'slug': ('title',)}
    
    # ✅ FIXED: Removed 'views' from fieldsets (it's editable=False in the model)
    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'slug', 'author', 'category', 'content')
        }),
        ('Media & SEO', {
            'fields': ('featured_image', 'meta_description')
        }),
        ('Status', {
            'fields': ('is_published',),
            'classes': ('collapse',)  # Hides this section by default
        }),
    )
    
    # Auto-fill author with current user
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set author on creation
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    # Show featured image preview in admin
    def featured_badge(self, obj):
        if obj.featured_image:
            return '🖼️ Yes'
        return '❌ No'
    featured_badge.short_description = 'Image'
    
    # Custom actions
    actions = ['make_published', 'make_unpublished']
    
    def make_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} post(s) published successfully.')
    make_published.short_description = "✅ Publish selected posts"
    
    def make_unpublished(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} post(s) unpublished.')
    make_unpublished.short_description = "❌ Unpublish selected posts"