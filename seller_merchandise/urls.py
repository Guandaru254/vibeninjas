
from sys import path


from django.urls import path
from . import views
urlpatterns = [
    path('orders/', views.seller_merchandise_order_list, name='seller_merchandise_order_list'),
]