from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('set-password/', views.set_password, name='set_password'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=CustomAuthenticationForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='home',
        http_method_names=['get', 'post']  # Permitir GET y POST
    ), name='logout'),
    path('confirmar-promocion/<str:codigo>/', views.confirmar_promocion, name='confirmar_promocion'),
]
