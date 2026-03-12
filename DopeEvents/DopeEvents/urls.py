from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Vibeninjas Admin'
admin.site.site_title = 'Vibeninjas Administration'
admin.site.index_title = 'Site Administration'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls')),
    path('payments/', include('payments.urls')), # Prefix added to avoid root conflict
    path('analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)