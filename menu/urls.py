from django.urls import path

from . import views

urlpatterns = [
    path('menu/', views.menu_cliente, name='menu'),
    path('menu/<int:pk>/', views.detalle_producto, name='detalle_producto'),
]
