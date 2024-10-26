from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from .forms import CasaForm
from .models import FotoCasa, Casa


# Create your views here.


def es_admin(user):
    return user.is_staff and not user.is_superuser


@login_required
@user_passes_test(es_admin)
def configuracion_admin(request):
    return render(request, "properties/configuracion_admin.html")


@login_required
@user_passes_test(es_admin)
def agregar_casa(request):
    if request.method == "POST":
        form = CasaForm(request.POST, request.FILES)
        if form.is_valid():
            casa = form.save(commit=False)
            casa.administrador = request.user
            casa.save()
            form.save_m2m()  # Para guardar las amenidades

            # Guardar las fotos
            for i, foto in enumerate(request.FILES.getlist("fotos")):
                FotoCasa.objects.create(casa=casa, imagen=foto, orden=i)

            messages.success(request, "Casa agregada exitosamente")
            return redirect("properties:configuracion")
    else:
        form = CasaForm()

    return render(request, "properties/agregar_casa.html", {"form": form})


@login_required
@user_passes_test(es_admin)
def lista_casas(request):
    casas = Casa.objects.filter(administrador=request.user)
    return render(request, "properties/lista_casas.html", {"casas": casas})


def detalle_casa(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id)
    context = {
        'casa': casa,
        'is_authenticated': request.user.is_authenticated,
        'is_admin': request.user.is_staff and not request.user.is_superuser if request.user.is_authenticated else False,
        'is_owner': request.user.is_authenticated and casa.administrador == request.user
    }
    return render(request, "properties/detalle_casa.html", context)


@login_required
@user_passes_test(es_admin)
def eliminar_casa(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    if request.method == "POST":
        casa.delete()
        messages.success(request, "Casa eliminada exitosamente")
        return redirect("properties:lista_casas")
    return render(request, "properties/confirmar_eliminar_casa.html", {"casa": casa})


@login_required
@user_passes_test(es_admin)
def gestionar_disponibilidad(request):
    # Obtener todas las casas del administrador con conteo de dispositivos activos
    casas = Casa.objects.filter(administrador=request.user).annotate(
        dispositivos_activos=Count("dispositivos", filter=Q(dispositivos__estado=True))
    )
    return render(request, "properties/gestionar_disponibilidad.html", {"casas": casas})


@login_required
@user_passes_test(es_admin)
def cambiar_disponibilidad(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    
    if request.method == "POST":
        casa.disponible = not casa.disponible
        casa.save()
        messages.success(
            request, 
            f"Casa {'activada' if casa.disponible else 'desactivada'} exitosamente"
        )
        return redirect("properties:gestionar_disponibilidad")
    
    return render(request, "properties/confirmar_cambio_disponibilidad.html", {
        "casa": casa,
        "accion": "activar" if not casa.disponible else "desactivar"
    })


def lista_casas_disponibles(request):
    casas = Casa.objects.filter(
        disponible=True,
        dispositivos__estado=True
    ).distinct()
    
    context = {
        'casas': casas,
        'is_authenticated': request.user.is_authenticated,
        'is_admin': request.user.is_staff and not request.user.is_superuser if request.user.is_authenticated else False
    }
    return render(request, "properties/lista_casas_disponibles.html", context)

