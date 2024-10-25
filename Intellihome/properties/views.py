from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import CasaForm
from .models import FotoCasa, Casa


# Create your views here.

def es_admin(user):
    return user.is_staff and not user.is_superuser

@login_required
@user_passes_test(es_admin)
def configuracion_admin(request):
    return render(request, 'properties/configuracion_admin.html')

@login_required
@user_passes_test(es_admin)
def agregar_casa(request):
    if request.method == 'POST':
        form = CasaForm(request.POST, request.FILES)
        if form.is_valid():
            casa = form.save(commit=False)
            casa.administrador = request.user
            casa.save()
            form.save_m2m()  # Para guardar las amenidades

            # Guardar las fotos
            for i, foto in enumerate(request.FILES.getlist('fotos')):
                FotoCasa.objects.create(
                    casa=casa,
                    imagen=foto,
                    orden=i
                )
            
            messages.success(request, 'Casa agregada exitosamente')
            return redirect('properties:configuracion')
    else:
        form = CasaForm()
    
    return render(request, 'properties/agregar_casa.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def lista_casas(request):
    casas = Casa.objects.filter(administrador=request.user)
    return render(request, 'properties/lista_casas.html', {'casas': casas})

@login_required
@user_passes_test(es_admin)
def detalle_casa(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    return render(request, 'properties/detalle_casa.html', {'casa': casa})

@login_required
@user_passes_test(es_admin)
def eliminar_casa(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    if request.method == 'POST':
        casa.delete()
        messages.success(request, 'Casa eliminada exitosamente')
        return redirect('properties:lista_casas')
    return render(request, 'properties/confirmar_eliminar_casa.html', {'casa': casa})
