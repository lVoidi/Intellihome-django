import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate  
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
import random  
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from .forms import UserRegistrationForm, VerificationCodeForm, SetPasswordForm, CustomAuthenticationForm, ForgotPasswordForm, UserProfileEditForm, PaymentInfoForm
from .models import PerfilUsuario, PromocionAdministrador, UsuarioAdicional, MetodoPago, ConfiguracionSistema, SystemStatus   
from properties.models import Casa
from .utils import enviar_mensaje, generar_codigo_verificacion
import string
from django.utils import timezone
from datetime import timedelta
from PIL import Image
import io
import base64
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Add this import at the top with other imports
from decimal import Decimal
from properties.models import Reserva
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

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
            
            # Guardar foto si existe
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
            
            if form.cleaned_data['incluir_pago']:
                return redirect('accounts:payment_info')
            else:
                codigo = ''.join(random.choices(string.digits, k=6))
                request.session['verification_code'] = codigo
                request.session['code_timestamp'] = timezone.now().isoformat()
                enviar_mensaje(user_data['email'], codigo)
                return redirect('accounts:verify_code')
    else:
        form = UserRegistrationForm()

def sistema_deshabilitado(request):
    return render(request, 'accounts/sistema_deshabilitado.html')
    
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
    payment_data = request.session.get('payment_info')
    
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
            
            if payment_data:
                perfil.nombre_tarjetahabiente = payment_data['nombre_tarjetahabiente']
                perfil.numero_tarjeta = payment_data['numero_tarjeta']
                perfil.fecha_validez = timezone.datetime.fromisoformat(payment_data['fecha_validez']).date()
                perfil.numero_verificador = payment_data['numero_verificador']
                perfil.marca_tarjeta = payment_data['marca_tarjeta']
                perfil.save()
            
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
            
            return redirect('accounts:login')
            
        return render(request, 'accounts/confirmar_promocion.html', {'promocion': promocion})
        
    except PromocionAdministrador.DoesNotExist:
        messages.error(request, 'Código de confirmación inválido o ya procesado')
        return redirect('accounts:login	')

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
        return redirect('properties:casas_disponibles')  # Cambiar 'home' por 'properties:casas_disponibles'
    context = {
        'titulo': 'Panel de Administración Principal'
    }
    return render(request, 'accounts/admin_home.html', context)

def staff_home(request):
    if not request.user.is_staff or request.user.is_superuser:
        return redirect('properties:casas_disponibles')  # Cambiar 'home' por 'properties:casas_disponibles'
    context = {
        'titulo': 'Panel de Subadministrador',
        'mensaje_bienvenida': '¡Bienvenido Subadministrador!'
    }
    return render(request, 'accounts/staff_home.html', context)

def user_home(request):
    return redirect('accounts:profile')

def custom_login(request):
    # Verificar el estado del sistema
    system_status = SystemStatus.objects.first()
    if system_status and not system_status.is_enabled:
        if request.method == 'POST':
            form = CustomAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    return redirect('admin:index')
                else:
                    messages.error(request, 'Acceso denegado. El sistema está deshabilitado.')
        else:
            form = CustomAuthenticationForm(request)
        return render(request, 'accounts/sistema_deshabilitado.html')

    # Sistema habilitado - proceso normal de login
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirigir según el tipo de usuario
            if user.is_superuser:
                return redirect('admin:index')
            elif user.is_staff:
                return redirect('accounts:staff_home')
            else:
                return redirect('accounts:user_home')
    else:
        form = CustomAuthenticationForm(request)
    
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

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                codigo = ''.join(random.choices(string.digits, k=6))
                request.session['reset_code'] = codigo
                request.session['reset_email'] = email
                request.session['code_timestamp'] = timezone.now().isoformat()
                
                mensaje = f"""
                Has solicitado restablecer tu contraseña.
                Tu código de verificación es: {codigo}
                Este código expirará en 2 minutos.
                """
                enviar_mensaje(email, mensaje)
                return redirect('accounts:verify_reset_code')
            except User.DoesNotExist:
                messages.error(request, 'El correo electrónico no está registrado en el sistema')
                return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})

def verify_reset_code(request):
    if 'reset_code' not in request.session:
        messages.error(request, 'Sesión inválida. Por favor, inicie el proceso nuevamente.')
        return redirect('accounts:login')
        
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['codigo'] == request.session['reset_code']:
                return redirect('accounts:reset_password')
            else:
                for key in ['reset_code', 'reset_email', 'code_timestamp']:
                    request.session.pop(key, None)
                messages.error(request, 'El código de verificación es incorrecto')
                return redirect('accounts:login')
    else:
        form = VerificationCodeForm()
    
    # Verificar tiempo
    code_timestamp = timezone.datetime.fromisoformat(request.session['code_timestamp'])
    tiempo_actual = timezone.now()
    tiempo_limite = code_timestamp + timedelta(minutes=2)
    segundos_restantes = int((tiempo_limite - tiempo_actual).total_seconds())
    
    if segundos_restantes <= 0:
        # Limpiar la sesión
        for key in ['reset_code', 'reset_email', 'code_timestamp']:
            request.session.pop(key, None)
        messages.error(request, 'El código ha expirado. Por favor, inicie el proceso nuevamente.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/verify_reset_code.html', {
        'form': form,
        'segundos_restantes': segundos_restantes
    })

def reset_password(request):
    if 'reset_email' not in request.session:
        messages.error(request, 'Sesión inválida')
        return redirect('accounts:login')
        
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(email=request.session['reset_email'])
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Limpiar sesión
            for key in ['reset_code', 'reset_email', 'code_timestamp']:
                request.session.pop(key, None)
                
            messages.success(request, 'Tu contraseña ha sido actualizada exitosamente')
            return redirect('accounts:login')
    else:
        form = SetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form})

@login_required
def edit_profile(request):
    try:
        perfil = request.user.perfilusuario
        if request.method == 'POST':
            form = UserProfileEditForm(request.POST, request.FILES, instance=perfil)
            if form.is_valid():
                # Guardar cambios del usuario
                user = request.user
                user.username = form.cleaned_data['username']
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
                
                # Guardar cambios del perfil
                perfil = form.save(commit=False)
                if 'foto_perfil' in request.FILES:
                    perfil.foto_perfil = request.FILES['foto_perfil']
                perfil.save()
                
                # Guardar relaciones many-to-many
                form.save_m2m()
                
                messages.success(request, 'Perfil actualizado exitosamente')
                return redirect('accounts:profile')
        else:
            form = UserProfileEditForm(instance=perfil)
        
        return render(request, 'accounts/edit_profile.html', {'form': form})
    except User.perfilusuario.RelatedObjectDoesNotExist:
        messages.error(request, 'Los datos del administrador no se pueden modificar')
        return redirect('accounts:profile')

def payment_info(request):
    if 'pending_registration' not in request.session:
        return redirect('accounts:register')
        
    if request.method == 'POST':
        form = PaymentInfoForm(request.POST)
        if form.is_valid():
            # Guardar información de pago en la sesión
            payment_data = {
                'nombre_tarjetahabiente': form.cleaned_data['nombre_tarjetahabiente'],
                'numero_tarjeta': form.cleaned_data['numero_tarjeta'],
                'fecha_validez': form.cleaned_data['fecha_validez'].isoformat(),
                'numero_verificador': form.cleaned_data['numero_verificador'],
                'marca_tarjeta': form.marca_tarjeta
            }
            request.session['payment_info'] = payment_data
            
            # Generar y enviar código de verificación
            codigo = ''.join(random.choices(string.digits, k=6))
            request.session['verification_code'] = codigo
            request.session['code_timestamp'] = timezone.now().isoformat()
            enviar_mensaje(request.session['pending_registration']['email'], codigo)
            return redirect('accounts:verify_code')
    else:
        form = PaymentInfoForm()
    
    return render(request, 'accounts/payment_info.html', {'form': form})

def index(request):
    if request.user.is_authenticated:
        if request.user.is_staff and not request.user.is_superuser:
            return redirect('accounts:staff_home')
        elif request.user.is_superuser:
            return redirect('admin:index')
    return redirect('properties:casas_disponibles')

@login_required
def gestionar_usuarios_adicionales(request):
    # Obtener usuarios que no son el usuario actual ni superusuarios
    usuarios_disponibles = User.objects.exclude(
        Q(id=request.user.id) | 
        Q(is_superuser=True) |
        Q(is_staff=True) |
        Q(es_adicional_de__usuario_principal=request.user)
    )
    
    usuarios_adicionales = UsuarioAdicional.objects.filter(
        usuario_principal=request.user
    )
    
    context = {
        'usuarios_disponibles': usuarios_disponibles,
        'usuarios_adicionales': usuarios_adicionales,
    }
    return render(request, 'accounts/gestionar_usuarios_adicionales.html', context)

@login_required
def agregar_usuario_adicional(request, user_id):
    usuario_a_agregar = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        UsuarioAdicional.objects.create(
            usuario_principal=request.user,
            usuario_adicional=usuario_a_agregar
        )
        messages.success(request, f"Se ha agregado a {usuario_a_agregar.username} como usuario adicional")
        return redirect('accounts:gestionar_usuarios_adicionales')
    
    return render(request, 'accounts/confirmar_agregar_adicional.html', {
        'usuario': usuario_a_agregar
    })

@login_required
def eliminar_usuario_adicional(request, user_id):
    relacion = get_object_or_404(UsuarioAdicional, 
                                usuario_principal=request.user, 
                                usuario_adicional_id=user_id)
    
    if request.method == "POST":
        relacion.delete()
        messages.success(request, "Usuario adicional eliminado exitosamente")
        return redirect('accounts:gestionar_usuarios_adicionales')
    
    return render(request, 'accounts/confirmar_eliminar_adicional.html', {
        'usuario': relacion.usuario_adicional
    })
    
@login_required
def user_profile(request):
    try:
        perfil = request.user.perfilusuario
        usuarios_adicionales = UsuarioAdicional.objects.filter(usuario_principal=request.user)
        
        context = {
            'user': request.user,
            'perfil': perfil,
            'usuarios_adicionales': usuarios_adicionales,
        }
        return render(request, 'accounts/user_profile.html', context)
    except User.perfilusuario.RelatedObjectDoesNotExist:
        messages.error(request, 'Perfil no encontrado')
        return redirect('home')

@login_required
def agregar_saldo(request):
    if request.method == 'POST':
        try:
            monto = Decimal(request.POST.get('monto', 0))
            cuotas = int(request.POST.get('cuotas', 1))
            metodo_pago_id = request.POST.get('metodo_pago')
            
            if not metodo_pago_id:
                messages.error(request, "Debe seleccionar un método de pago")
                return redirect('accounts:user_home')
            
            metodo_pago = get_object_or_404(MetodoPago, id=metodo_pago_id, usuario=request.user.perfilusuario)
            
            if monto <= 0:
                messages.error(request, "El monto debe ser mayor a 0")
                return redirect('accounts:user_home')
            
            perfil = request.user.perfilusuario
            perfil.agregar_saldo(monto)
            
            # Intentar enviar el correo con la información del método de pago usado
            try:
                subject = 'Factura de Recarga de Saldo - IntelliHome'
                message = f"""
                Factura Electrónica
                -------------------
                Usuario: {request.user.get_full_name()}
                Monto: ${monto}
                Cuotas: {cuotas}
                Método de Pago: {metodo_pago.marca_tarjeta} terminada en {metodo_pago.numero_tarjeta[-4:]}
                Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                enviar_mensaje(request.user.email, 0, message=message, subject="Factura de Recarga de Saldo - IntelliHome")
            except Exception as e:
                print(f"Error enviando correo: {str(e)}")
            
            messages.success(request, f"Se han agregado ${monto} a tu saldo")
            
        except (ValueError, decimal.InvalidOperation):
            messages.error(request, "Monto inválido")
        except Exception as e:
            messages.error(request, "Ocurrió un error al procesar el pago")
            print(f"Error en agregar_saldo: {str(e)}")
    
    return redirect('accounts:user_home')

@login_required
def profile(request):
    perfil = request.user.perfilusuario
    usuarios_adicionales = UsuarioAdicional.objects.filter(usuario_principal=request.user)
    
    # Obtener todas las reservas activas (pagadas o confirmadas)
    reservas_activas = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['PAGADA', 'CONFIRMADA', 'TEMPORAL']
    ).select_related('casa__estilo')
    
    # Filtrar las reservas expiradas y calcular tiempo restante
    reservas_vigentes = []
    for reserva in reservas_activas:
        if not reserva.esta_expirada():
            reserva.tiempo_restante = reserva.tiempo_restante_pago()
            reservas_vigentes.append(reserva)
    
    context = {
        'perfil': perfil,
        'reservas_activas': reservas_vigentes,
        'usuarios_adicionales': usuarios_adicionales,
    }
    return render(request, 'accounts/user_profile.html', context)

@login_required
def agregar_metodo_pago(request):
    if request.method == 'POST':
        form = PaymentInfoForm(request.POST)
        if form.is_valid():
            perfil = request.user.perfilusuario
            
            # Si es el primer método de pago, hacerlo principal
            es_principal = not perfil.metodos_pago.exists()
            
            MetodoPago.objects.create(
                usuario=perfil,
                nombre_tarjetahabiente=form.cleaned_data['nombre_tarjetahabiente'],
                numero_tarjeta=form.cleaned_data['numero_tarjeta'],
                fecha_validez=form.cleaned_data['fecha_validez'],
                numero_verificador=form.cleaned_data['numero_verificador'],
                marca_tarjeta=form.marca_tarjeta,
                es_principal=es_principal
            )
            
            messages.success(request, f"Método de pago agregado exitosamente")
            return redirect('accounts:profile')  # Cambiado de user_home a profile
        else:
            messages.error(request, "Por favor, verifica los datos ingresados")
    
    return redirect('accounts:profile')  

@login_required
def establecer_metodo_pago_principal(request, metodo_id):
    metodo = get_object_or_404(MetodoPago, id=metodo_id, usuario=request.user.perfilusuario)
    
    # Quitar el estado principal de todos los métodos
    MetodoPago.objects.filter(usuario=request.user.perfilusuario).update(es_principal=False)
    
    # Establecer el nuevo método principal
    metodo.es_principal = True
    metodo.save()
    
    messages.success(request, "Método de pago principal actualizado")
    return redirect('accounts:user_home')

@login_required
def eliminar_metodo_pago(request, metodo_id):
    metodo = get_object_or_404(MetodoPago, id=metodo_id, usuario=request.user.perfilusuario)
    
    if metodo.es_principal:
        # Si hay otros métodos, hacer el más reciente principal
        siguiente_metodo = MetodoPago.objects.filter(
            usuario=request.user.perfilusuario
        ).exclude(id=metodo_id).first()
        
        if siguiente_metodo:
            siguiente_metodo.es_principal = True
            siguiente_metodo.save()
    
    metodo.delete()
    messages.success(request, "Método de pago eliminado")
    return redirect('accounts:user_home')

@staff_member_required
def limpiar_inquilinos(request):
    if request.method == "POST":
        # Obtener todas las reservas activas
        reservas_activas = Reserva.objects.filter(estado='CONFIRMADA')
        
        # Guardar la información necesaria antes de eliminar
        reservas_info = [(reserva.usuario.email, reserva.casa) for reserva in reservas_activas]
        
        # Registrar la cantidad de reservas que se eliminarán
        cantidad_reservas = reservas_activas.count()
        
        # Actualizar el estado de las casas y limpiar todas las reservas
        for reserva in reservas_activas:
            casa = reserva.casa
            casa.disponible = True  # Marcar la casa como disponible
            casa.save()
            
            # Eliminar todas las reservas asociadas a esta casa
            Reserva.objects.filter(casa=casa).delete()

        # Eliminar todas las reservas activas
        reservas_activas.delete()
        
        messages.success(
            request, 
            f"Se han eliminado {cantidad_reservas} reservas activas exitosamente"
        )
        
        # Enviar notificación a los usuarios afectados
        for email, casa in reservas_info:
            mensaje = f"""
            Le informamos que su reserva para la casa {casa.estilo.nombre} ha sido cancelada 
            por el administrador del sistema como parte de una limpieza general de inquilinos.
            
            Si tiene alguna pregunta, por favor contacte al administrador.
            """
            try:
                enviar_mensaje(
                    email,
                    0,
                    message=mensaje,
                    subject="Cancelación de Reserva - IntelliHome"
                )
            except Exception as e:
                print(f"Error enviando notificación a {email}: {str(e)}")
    
    return redirect('accounts:staff_home')

    
@login_required
def check_pagos_pendientes(request):
    reservas = Reserva.objects.filter(
        usuario=request.user,
        estado='CONFIRMADA'
    )
    
    necesita_refresh = False
    for reserva in reservas:
        if reserva.minutos_hasta_proximo_pago <= 0:
            # Si han pasado más de 5 días (equivalente a ~1 minuto en tiempo simulado)
            if reserva.dias_hasta_proximo_pago < -5:
                reserva.estado = 'CANCELADA'
                reserva.save()
                necesita_refresh = True
    
    return JsonResponse({'necesita_refresh': necesita_refresh})

@staff_member_required
def gestionar_usuarios(request):
    usuarios_activos = PerfilUsuario.objects.filter(esta_habilitado=True)
    usuarios_deshabilitados = PerfilUsuario.objects.filter(esta_habilitado=False)
    
    context = {
        'usuarios_activos': usuarios_activos,
        'usuarios_deshabilitados': usuarios_deshabilitados,
    }
    return render(request, 'accounts/gestionar_usuarios.html', context)

@staff_member_required
def deshabilitar_usuario(request, user_id):
    if request.method == "POST":
        perfil = get_object_or_404(PerfilUsuario, user_id=user_id)
        razon = request.POST.get('razon', '')
        
        # Deshabilitar usuario
        perfil.esta_habilitado = False
        perfil.razon_deshabilitado = razon
        perfil.fecha_deshabilitado = timezone.now()
        perfil.save()
        
        # Desactivar usuario en Django
        perfil.user.is_active = False
        perfil.user.save()
        
        # Liberar casas rentadas
        Reserva.objects.filter(
            usuario=perfil.user,
            estado='CONFIRMADA'
        ).update(estado='CANCELADA')
        
        messages.success(request, f"Usuario {perfil.user.username} deshabilitado exitosamente")
    return redirect('accounts:gestionar_usuarios')

@staff_member_required
def habilitar_usuario(request, user_id):
    if request.method == "POST":
        perfil = get_object_or_404(PerfilUsuario, user_id=user_id)
        
        # Habilitar usuario
        perfil.esta_habilitado = True
        perfil.razon_deshabilitado = None
        perfil.fecha_deshabilitado = None
        perfil.save()
        
        # Activar usuario en Django
        perfil.user.is_active = True
        perfil.user.save()
        
        messages.success(request, f"Usuario {perfil.user.username} habilitado exitosamente")
    return redirect('accounts:gestionar_usuarios')


