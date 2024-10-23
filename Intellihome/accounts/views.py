from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
import random  
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from .forms import UserRegistrationForm, VerificationCodeForm, SetPasswordForm
from .models import PerfilUsuario
from .utils import enviar_mensaje
import string

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_unusable_password()  # Usuario sin contraseña inicial
            user.is_active = False  # Inactivo hasta verificar
            user.save()
            
            codigo = ''.join(random.choices(string.digits, k=6))
            perfil = PerfilUsuario.objects.create(
                user=user,
                fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                foto_perfil=form.cleaned_data.get('foto_perfil'),
                incluir_pago=form.cleaned_data['incluir_pago'],
                codigo_verificacion=codigo
            )
            perfil.estilos_casa.set(form.cleaned_data['estilos_casa'])
            perfil.tipos_transporte.set(form.cleaned_data['tipos_transporte'])
            
            enviar_mensaje(user.email, codigo)
            request.session['pending_user_id'] = user.id
            return redirect('accounts:verify_code')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_code(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:register')
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(id=user_id)
                perfil = PerfilUsuario.objects.get(user=user)
                if perfil.codigo_verificacion == form.cleaned_data['codigo']:
                    return redirect('accounts:set_password')
                else:
                    form.add_error('codigo', 'Código de verificación incorrecto')
            except (User.DoesNotExist, PerfilUsuario.DoesNotExist):
                return redirect('accounts:register')
    else:
        form = VerificationCodeForm()
    
    return render(request, 'accounts/verify_code.html', {'form': form})

def set_password(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:register')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(id=user_id)
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.save()
                perfil = PerfilUsuario.objects.get(user=user)
                perfil.email_verificado = True
                perfil.save()
                del request.session['pending_user_id']
                messages.success(request, 'Registro completado exitosamente')
                return redirect('accounts:login')
            except (User.DoesNotExist, PerfilUsuario.DoesNotExist):
                return redirect('accounts:register')
    else:
        form = SetPasswordForm()
    
    return render(request, 'accounts/set_password.html', {'form': form})
