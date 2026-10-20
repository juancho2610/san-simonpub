#Pestañas de navegacion
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(
        template_name='usuarios/login.html',
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('panel/admin/', views.panel_admin, name='panel_admin'),
    path('panel/servicio/', views.panel_servicio, name='panel_servicio'),
    path('panel/cocina/', views.panel_cocina, name='panel_cocina'),
    path('panel/cliente/', views.panel_cliente, name='panel_cliente'),
]
