from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.LoginConCaptcha.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('recuperar/', views.RecuperarConCaptcha.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('recuperar/listo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/password_reset_complete.html'), name='password_reset_complete'),
    path('panel/admin/', views.panel_admin, name='panel_admin'),
    path('panel/servicio/', views.panel_servicio, name='panel_servicio'),
    path('panel/cocina/', views.panel_cocina, name='panel_cocina'),
    path('panel/cliente/', views.panel_cliente, name='panel_cliente'),
]
