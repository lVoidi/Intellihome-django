from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate  
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
import random  
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from .forms import UserRegistrationForm, VerificationCodeForm, SetPasswordForm, CustomAuthenticationForm
from .models import PerfilUsuario, PromocionAdministrador
from .utils import enviar_mensaje
import string
from django.utils import timezone
from datetime import timedelta
from PIL import Image
import io
import base64

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
                foto = request.FILES['foto_perfil']
                import base64
                import io
                from PIL import Image

                # Procesar la imagen
                img = Image.open(foto)
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                img_io.seek(0)
                foto_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
                
                request.session['pending_photo'] = {
                    'name': foto.name,
                    'content': foto_base64,
                    'content_type': 'image/jpeg'
                }
            
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
            
            # Crear el perfil primero
            perfil = PerfilUsuario.objects.create(
                user=user,
                fecha_nacimiento=timezone.datetime.fromisoformat(registration_data['fecha_nacimiento']).date(),
                incluir_pago=registration_data['incluir_pago'],
                email_verificado=True
            )

            # Procesar y guardar la foto si existe
            foto_data = request.session.get('pending_photo')
            if foto_data:
                import base64
                from django.core.files.base import ContentFile
                
                # Decodificar la foto y guardarla
                foto_content = base64.b64decode(foto_data['content'])
                foto_file = ContentFile(foto_content, name=foto_data['name'])
                perfil.foto_perfil.save(foto_data['name'], foto_file, save=True)
            
            perfil.estilos_casa.set(registration_data['estilos_casa'])
            perfil.tipos_transporte.set(registration_data['tipos_transporte'])
            
            # Limpiar datos de la sesión
            for key in ['pending_registration', 'verification_code', 'code_timestamp', 'verification_attempts', 'pending_photo']:
                request.session.pop(key, None)
                
            messages.success(request, 'Registro completado exitosamente')
            return redirect('accounts:login')
    else:
        form = SetPasswordForm()
    
    return render(request, 'accounts/set_password.html', {'form': form})

def confirmar_promocion(request, codigo=None):
    # Si no hay usuario autenticado, redirigir al login
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para confirmar la promoción.')
        return redirect('accounts:login')
    
    try:
        promocion = PromocionAdministrador.objects.filter(
            codigo_confirmacion=codigo,
            estado='pendiente'
        ).latest('fecha_solicitud')
        
        if request.method == 'POST':
            accion = request.POST.get('accion')
            if accion == 'aceptar':
                # Marcar todas las promociones anteriores como rechazadas
                PromocionAdministrador.objects.filter(
                    usuario=promocion.usuario,
                    estado='pendiente'
                ).exclude(id=promocion.id).update(estado='rechazada')
                
                promocion.estado = 'aceptada'
                promocion.save()
                
                usuario = promocion.usuario
                usuario.is_staff = True
                usuario.save()
                
                messages.success(request, 'Has aceptado la promoción. Podrás ver tu nuevo rol cuando inicies sesión.')
            elif accion == 'rechazar':
                promocion.estado = 'rechazada'
                promocion.save()
                messages.info(request, 'Has rechazado la promoción a administrador.')
            
            return redirect('home')
            
        return render(request, 'accounts/confirmar_promocion.html', {'promocion': promocion})
        
    except PromocionAdministrador.DoesNotExist:
        messages.error(request, 'Código de confirmación inválido o ya procesado')
        return redirect('home')

def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('accounts:admin_home')
        elif request.user.is_staff:
            return redirect('accounts:staff_home')
        else:
            return redirect('accounts:user_home')
    return render(request, 'home.html')

def admin_home(request):
    if not request.user.is_superuser:
        return redirect('home')
    context = {
        'titulo': 'Panel de Administración Principal'
    }
    return render(request, 'accounts/admin_home.html', context)

def staff_home(request):
    if not request.user.is_staff or request.user.is_superuser:
        return redirect('home')
    context = {
        'titulo': 'Panel de Subadministrador',
        'mensaje_bienvenida': '¡Bienvenido Subadministrador!'
    }
    return render(request, 'accounts/staff_home.html', context)

def user_home(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('home')
    context = {
        'titulo': 'Mi Portal de Usuario'
    }
    return render(request, 'accounts/user_home.html', context)

def custom_login(request):
    if request.user.is_authenticated:
        return redirect_based_on_user_type(request.user)
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect_based_on_user_type(user)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def redirect_based_on_user_type(user):
    try:
        if user.is_superuser:
            return redirect('accounts:admin_home')
            
        if user.is_staff:
            promocion = PromocionAdministrador.objects.filter(
                usuario=user,
                estado='aceptada'
            ).latest('fecha_solicitud')
            return redirect('accounts:staff_home')
            
        revocado = PromocionAdministrador.objects.filter(
            usuario=user,
            codigo_confirmacion='REVOKED'
        ).exists()
        
        return redirect('accounts:user_home')
        
    except PromocionAdministrador.DoesNotExist:
        return redirect('accounts:user_home')
