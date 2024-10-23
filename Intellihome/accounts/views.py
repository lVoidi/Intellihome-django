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
from django.utils import timezone
from datetime import timedelta

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
           
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'fecha_nacimiento': form.cleaned_data['fecha_nacimiento'].isoformat(),
                'incluir_pago': form.cleaned_data['incluir_pago'],
                'estilos_casa': [estilo.id for estilo in form.cleaned_data['estilos_casa']],
                'tipos_transporte': [tipo.id for tipo in form.cleaned_data['tipos_transporte']],
            }
            
            if 'foto_perfil' in request.FILES:
                # Manejar la foto de perfil temporalmente si es necesario
                pass
            
            request.session['pending_registration'] = user_data
            codigo = ''.join(random.choices(string.digits, k=6))
            request.session['verification_code'] = codigo
            request.session['code_timestamp'] = timezone.now().isoformat()
            
            enviar_mensaje(form.cleaned_data['email'], codigo)
            return redirect('accounts:verify_code')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_code(request):
    registration_data = request.session.get('pending_registration')
    verification_code = request.session.get('verification_code')
    
    if not registration_data or not verification_code:
        return redirect('accounts:register')
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['codigo'] == verification_code:
                return redirect('accounts:set_password')
            else:
                intentos = request.session.get('verification_attempts', 0) + 1
                request.session['verification_attempts'] = intentos
                
                if intentos >= 2:
                    messages.error(request, 'Superaste la cantidad de intentos para escribir el código de verificación')
                    # Limpiar datos de la sesión
                    for key in ['pending_registration', 'verification_code', 'code_timestamp', 'verification_attempts']:
                        request.session.pop(key, None)
                    return redirect('accounts:register')
                
                form.add_error('codigo', 'Código de verificación incorrecto')
    else:
        form = VerificationCodeForm()
    
    # Calcular tiempo restante
    code_timestamp = timezone.datetime.fromisoformat(request.session.get('code_timestamp'))
    tiempo_actual = timezone.now()
    tiempo_limite = code_timestamp + timedelta(minutes=2)
    segundos_restantes = int((tiempo_limite - tiempo_actual).total_seconds())
    
    if segundos_restantes <= 0:
        messages.error(request, 'El código ha expirado')
        return redirect('accounts:register')
    
    return render(request, 'accounts/verify_code.html', {
        'form': form,
        'segundos_restantes': segundos_restantes
    })

def set_password(request):
    registration_data = request.session.get('pending_registration')
    if not registration_data:
        return redirect('accounts:register')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            
            user = User.objects.create_user(
                username=registration_data['username'],
                email=registration_data['email'],
                password=form.cleaned_data['password1'],
                first_name=registration_data['first_name'],
                last_name=registration_data['last_name'],
                is_active=True
            )
            
            perfil = PerfilUsuario.objects.create(
                user=user,
                fecha_nacimiento=timezone.datetime.fromisoformat(registration_data['fecha_nacimiento']).date(),
                incluir_pago=registration_data['incluir_pago'],
                email_verificado=True
            )
            
            perfil.estilos_casa.set(registration_data['estilos_casa'])
            perfil.tipos_transporte.set(registration_data['tipos_transporte'])
            
            # Limpiar datos de la sesión
            for key in ['pending_registration', 'verification_code', 'code_timestamp', 'verification_attempts']:
                request.session.pop(key, None)
                
            messages.success(request, 'Registro completado exitosamente')
            return redirect('accounts:login')
    else:
        form = SetPasswordForm()
    
    return render(request, 'accounts/set_password.html', {'form': form})
