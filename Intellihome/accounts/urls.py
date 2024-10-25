from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('set-password/', views.set_password, name='set_password'),
    path('login/', views.custom_login, name='login'),  # Reemplazamos la vista de login
    path('logout/', auth_views.LogoutView.as_view(
        next_page='home',
        http_method_names=['get', 'post']  # Permitir GET y POST
    ), name='logout'),
    path('confirmar-promocion/<str:codigo>/', views.confirmar_promocion, name='confirmar_promocion'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('staff-home/', views.staff_home, name='staff_home'),
    path('user-home/', views.user_home, name='user_home'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('payment-info/', views.payment_info, name='payment_info'),
]
