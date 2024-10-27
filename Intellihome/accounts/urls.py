from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),  # Agregar esta línea
    path('register/', views.register, name='register'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('set-password/', views.set_password, name='set_password'),
    path('login/', views.custom_login, name='login'),  # Reemplazamos la vista de login
    path('logout/', auth_views.LogoutView.as_view(
        next_page='properties:casas_disponibles',  # Cambiado de 'accounts:home' a 'home'
        http_method_names=['get', 'post']
    ), name='logout'),
    path('confirmar-promocion/<str:codigo>/', views.confirmar_promocion, name='confirmar_promocion'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('staff-home/', views.staff_home, name='staff_home'),
    path('profile/', views.profile, name='profile'),
    path('user-home/', views.user_home, name='user_home'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('payment-info/', views.payment_info, name='payment_info'),
    path('usuarios-adicionales/', views.gestionar_usuarios_adicionales, name='gestionar_usuarios_adicionales'),
    path('usuario-adicional/agregar/<int:user_id>/', views.agregar_usuario_adicional, name='agregar_usuario_adicional'),
    path('usuario-adicional/eliminar/<int:user_id>/', views.eliminar_usuario_adicional, name='eliminar_usuario_adicional'),
    path('agregar-saldo/', views.agregar_saldo, name='agregar_saldo'),
    path('agregar-metodo-pago/', views.agregar_metodo_pago, name='agregar_metodo_pago'),
    path('metodo-pago/<int:metodo_id>/eliminar/', views.eliminar_metodo_pago, name='eliminar_metodo_pago'),
    path('metodo-pago/<int:metodo_id>/principal/', views.establecer_metodo_pago_principal, name='establecer_metodo_pago_principal'),
    path('limpiar-inquilinos/', views.limpiar_inquilinos, name='limpiar_inquilinos'),
    path('check-pagos-pendientes/', views.check_pagos_pendientes, name='check_pagos_pendientes'),
    path('gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('deshabilitar-usuario/<int:user_id>/', views.deshabilitar_usuario, name='deshabilitar_usuario'),
    path('habilitar-usuario/<int:user_id>/', views.habilitar_usuario, name='habilitar_usuario'),
]
