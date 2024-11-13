from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from properties.models import Casa
from .models import DispositivoIoT, TipoDispositivo
from .forms import DispositivoIoTForm
from .utils import notify_iot_server
from accounts.models import UsuarioAdicional
from django.db.models import Q
from django.utils import timezone


def es_admin(user):
    return user.is_staff and not user.is_superuser


@login_required
@user_passes_test(es_admin)
def lista_casas_dispositivos(request):
    casas = Casa.objects.filter(administrador=request.user)
    return render(request, "devices/lista_casas.html", {"casas": casas})


@login_required
@user_passes_test(es_admin)
def gestionar_dispositivos(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    dispositivos = DispositivoIoT.objects.filter(casa=casa)

    if request.method == "POST":
        form = DispositivoIoTForm(request.POST)
        if form.is_valid():
            dispositivo = form.save(commit=False)
            dispositivo.casa = casa
            dispositivo.save()

            messages.success(request, "Dispositivo agregado exitosamente")
            return redirect("devices:gestionar_dispositivos", casa_id=casa.id)
    else:
        form = DispositivoIoTForm()

    return render(
        request,
        "devices/gestionar_dispositivos.html",
        {"casa": casa, "dispositivos": dispositivos, "form": form},
    )


@login_required
@user_passes_test(es_admin)
def cambiar_estado(request, dispositivo_id):
    dispositivo = get_object_or_404(
        DispositivoIoT, id=dispositivo_id, casa__administrador=request.user
    )
    if request.method == "POST":
        dispositivo.estado = not dispositivo.estado
        dispositivo.save()
        messages.success(
            request,
            f"Estado del dispositivo {dispositivo.nombre} actualizado exitosamente",
        )
    return redirect("devices:gestionar_dispositivos", casa_id=dispositivo.casa.id)


@login_required
@user_passes_test(es_admin)
def eliminar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(
        DispositivoIoT, id=dispositivo_id, casa__administrador=request.user
    )
    if request.method == 'POST':
        casa_id = dispositivo.casa.id
        
        dispositivo.delete()
        messages.success(request, 'Dispositivo eliminado exitosamente')
        return redirect('devices:gestionar_dispositivos', casa_id=casa_id)
    return redirect('devices:gestionar_dispositivos', casa_id=dispositivo.casa.id)


@login_required
def mis_dispositivos(request):
    try:
        relacion_adicional = UsuarioAdicional.objects.get(usuario_adicional=request.user)
        usuario_principal = relacion_adicional.usuario_principal
        # Obtener casas del usuario principal
        casas = Casa.objects.filter(
            reserva__usuario=usuario_principal,
            reserva__estado='PAGADA',
            reserva__fecha_ultimo_pago__gt=timezone.now() - timezone.timedelta(minutes=5)
        ).distinct()
    except UsuarioAdicional.DoesNotExist:
        # Si no es usuario adicional, obtener sus propias casas
        casas = Casa.objects.filter(
            reserva__usuario=request.user,
            reserva__estado='PAGADA',
            reserva__fecha_ultimo_pago__gt=timezone.now() - timezone.timedelta(minutes=5)
        ).distinct()
    
    dispositivos_por_casa = {}
    for casa in casas:
        dispositivos_por_casa[casa] = casa.dispositivos.all()
    
    return render(request, 'devices/mis_dispositivos.html', {
        'dispositivos_por_casa': dispositivos_por_casa,
        'es_adicional': hasattr(request.user, 'usuarioadicional')
    })

@login_required
def probar_dispositivo(request, dispositivo_id):
    if request.method == 'POST':
        dispositivo = get_object_or_404(DispositivoIoT, id=dispositivo_id)
        
        # Verificar si el usuario tiene acceso al dispositivo
        if request.user.is_staff:
            if dispositivo.casa.administrador != request.user:
                return JsonResponse({'success': False, 'message': 'No autorizado'})
        else:
            # Verificar si el usuario es principal o adicional con acceso a la casa
            try:
                tiene_acceso = Casa.objects.filter(
                    Q(reserva__usuario=request.user) |
                    Q(reserva__usuario__usuario_adicional=request.user),
                    id=dispositivo.casa.id,
                    reserva__estado='CONFIRMADA'
                ).exists()
                print(tiene_acceso)
                if not tiene_acceso:
                    return JsonResponse({'success': False, 'message': 'No autorizado'})
            except Exception as e:
                print(e)
                pass
        print(dispositivo.tipo.nombre, dispositivo.id)
        success = notify_iot_server('toggle', {
            'id': dispositivo.id,
            'type': dispositivo.tipo.nombre
        })
        
        return JsonResponse({
            'success': success,
            'message': 'Prueba exitosa' if success else 'Error al probar el dispositivo'
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})