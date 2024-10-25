from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from properties.models import Casa
from .models import DispositivoIoT, TipoDispositivo
from .forms import DispositivoIoTForm
from .utils import notify_iot_server


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

            # Notificar al servidor IoT
            notify_iot_server(
                "add", {"id": dispositivo.id, "type": dispositivo.tipo.nombre.lower()}
            )

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
        
        # Notificar al servidor IoT antes de eliminar
        notify_iot_server("delete", {
            "id": dispositivo.id
        })
        
        dispositivo.delete()
        messages.success(request, 'Dispositivo eliminado exitosamente')
        return redirect('devices:gestionar_dispositivos', casa_id=casa_id)
    return redirect('devices:gestionar_dispositivos', casa_id=dispositivo.casa.id)
