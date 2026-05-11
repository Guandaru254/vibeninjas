from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
import json
import os

admin.site.site_header = 'Zozaprime Admin'
admin.site.site_title = 'Zozaprime Administration'
admin.site.index_title = 'Site Administration'

# Serve manifest.json
def serve_manifest(request):
    manifest = {
        "name": "ZOZAPRIME",
        "short_name": "ZOZAPRIME",
        "description": "Zozaprime is Kenya's smartest event ticketing platform — M-Pesa native, International payments & audience analytics built in. Sell tickets faster. Know your audience",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#fff",
        "theme_color": "#ff4d4d",
        "orientation": "portrait-primary",
        "scope": "/",
        "icons": [
            {
                "src": "/static/img/logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/img/apple-touch-icon.png",
                "sizes": "180x180",
                "type": "image/png"
            },
            {
                "src": "/static/img/favicon.png",
                "sizes": "32x32",
                "type": "image/png"
            }
        ],
        "categories": ["entertainment", "lifestyle", "music"],
        "shortcuts": [
            {
                "name": "Browse Events",
                "short_name": "Events",
                "url": "/events/",
                "icons": [{"src": "/static/img/favicon.png", "sizes": "32x32"}]
            }
        ]
    }
    return JsonResponse(manifest)


# ============================================================
# SEO & GEO — Serve root-level files (llms.txt, sitemap.xml, robots.txt)
# ============================================================

def serve_llms_txt(request):
    """Serve llms.txt for AI search engines (ChatGPT, Claude, Perplexity, Gemini)."""
    file_path = os.path.join(settings.BASE_DIR, 'llms.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
    except FileNotFoundError:
        return HttpResponse('llms.txt not found', status=404, content_type='text/plain')


def serve_sitemap_xml(request):
    """Serve sitemap.xml for search engine indexing."""
    file_path = os.path.join(settings.BASE_DIR, 'sitemap.xml')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/xml; charset=utf-8')
    except FileNotFoundError:
        return HttpResponse('sitemap.xml not found', status=404, content_type='text/plain')


def serve_robots_txt(request):
    """Serve robots.txt for search engine crawler instructions."""
    file_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
    except FileNotFoundError:
        return HttpResponse('robots.txt not found', status=404, content_type='text/plain')


def serve_bing_site_auth(request):
    """Serve BingSiteAuth.xml for Bing Webmaster Tools verification."""
    file_path = os.path.join(settings.BASE_DIR, 'BingSiteAuth.xml')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/xml; charset=utf-8')
    except FileNotFoundError:
        return HttpResponse('BingSiteAuth.xml not found', status=404, content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls')),
    path('payments/', include('payments.urls')),
    path('analytics/', include('analytics.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('blog/', include('blog.urls', namespace='blog')),

    # PWA files
    path('manifest.json', serve_manifest, name='manifest'),
    path('sw.js', TemplateView.as_view(
        template_name='sw.js',
        content_type='application/javascript'
    ), name='sw'),

    # SEO & GEO files (root-level)
    path('llms.txt', serve_llms_txt, name='llms_txt'),
    path('sitemap.xml', serve_sitemap_xml, name='sitemap_xml'),
    path('robots.txt', serve_robots_txt, name='robots_txt'),
    path('BingSiteAuth.xml', serve_bing_site_auth, name='bing_site_auth'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)