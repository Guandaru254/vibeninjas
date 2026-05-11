from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='list'), # This 'list' name is used in the base.html link
    path('<slug:slug>/', views.BlogDetailView.as_view(), name='detail'),
]