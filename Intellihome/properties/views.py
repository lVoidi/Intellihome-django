from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .forms import CasaForm, RangoFechasForm, ReservaForm
from .models import FotoCasa, Casa, Reserva, ConfiguracionTiempoSimulado
from datetime import datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from decimal import Decimal
from django.http import JsonResponse


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
    form = RangoFechasForm(request.GET or None)
    casas_query = Casa.objects.filter(disponible=True)
    casas_no_disponibles = set()
    
    if form.is_valid():
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        
        # Obtener solo las reservas CONFIRMADAS que se solapan con el rango seleccionado
        reservas = Reserva.objects.filter(
            Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio),
            estado='CONFIRMADA'  # Mover el filtro de estado al final
        )
        casas_no_disponibles = set(reserva.casa.id for reserva in reservas)
    if request.user.is_authenticated:
        usuarios_principales = request.user.es_adicional_de.values_list('usuario_principal', flat=True)
        casas_query = casas_query.filter(
            Q(dispositivos__estado=True) |
            Q(administrador__in=usuarios_principales)
        )
    else:
        casas_query = casas_query.filter(dispositivos__estado=True)
    
    casas = casas_query.distinct()
    
    context = {
        'casas': casas,
        'form': form,
        'casas_no_disponibles': casas_no_disponibles,
        'is_authenticated': request.user.is_authenticated,
        'is_admin': request.user.is_staff and not request.user.is_superuser if request.user.is_authenticated else False
    }
    return render(request, "properties/lista_casas_disponibles.html", context)

@login_required
def reservar_casa(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id)
    
    if request.method == "POST":
        form = ReservaForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            es_indefinida = request.POST.get('es_indefinida') == 'on'
            
            # Verificar disponibilidad
            reservas_existentes = Reserva.objects.filter(
                casa=casa,
                estado='CONFIRMADA', 
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            )
            
            if reservas_existentes.exists():
                messages.error(request, "La casa no está disponible para las fechas seleccionadas")
                return redirect('properties:detalle_casa', casa_id=casa_id)
            
            # Crear la reserva
            reserva = Reserva.objects.create(
            casa=casa,
            usuario=request.user,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            es_indefinida=es_indefinida,
            estado='TEMPORAL',  
            fecha_reserva=timezone.now()  
           )
            
            messages.success(request, "Casa reservada exitosamente. Por favor, diríjase a su perfil para realizar el pago.")
            return redirect('accounts:profile')  # Redirigir al perfil del usuario
    else:
        form = ReservaForm()
    
    return render(request, 'properties/reservar_casa.html', {
        'form': form,
        'casa': casa
    })

@login_required
@user_passes_test(es_admin)
def configurar_tiempo_simulado(request):
    config = ConfiguracionTiempoSimulado.objects.first()
    if not config:
        config = ConfiguracionTiempoSimulado.objects.create(
            modificado_por=request.user
        )

    if request.method == "POST":
        minutos_por_mes = request.POST.get('minutos_por_mes')
        minutos_reserva = request.POST.get('minutos_reserva_temporal')
        
        if minutos_por_mes and minutos_reserva:
            config.minutos_por_mes = int(minutos_por_mes)
            config.minutos_reserva_temporal = int(minutos_reserva)
            config.modificado_por = request.user
            config.save()
            messages.success(request, "Configuración actualizada exitosamente")
            return redirect('properties:configuracion_admin')

    return render(request, 'properties/configurar_tiempo.html', {'config': config})




@login_required
@user_passes_test(es_admin)
def ver_inquilinos(request, casa_id):
    casa = get_object_or_404(Casa, id=casa_id, administrador=request.user)
    
    # Obtener la reserva activa
    reserva_activa = Reserva.objects.filter(
        casa=casa,
        estado='CONFIRMADA'
    ).select_related('usuario__perfilusuario').first()
    
    usuarios_adicionales = []
    if reserva_activa:
        # Obtener usuarios adicionales del inquilino principal
        usuarios_adicionales = User.objects.filter(
            es_adicional_de__usuario_principal=reserva_activa.usuario
        ).select_related('perfilusuario')
    
    context = {
        'casa': casa,
        'reserva_activa': reserva_activa,
        'usuarios_adicionales': usuarios_adicionales,
    }
    return render(request, 'properties/inquilinos_casa.html', context)


@login_required
@user_passes_test(es_admin)
def reporte_alquileres(request):
    # Obtener el mes y año seleccionados del query string
    mes = request.GET.get('mes', timezone.now().month)
    anio = request.GET.get('anio', timezone.now().year)
    
    try:
        mes = int(mes)
        anio = int(anio)
    except (ValueError, TypeError):
        mes = timezone.now().month
        anio = timezone.now().year
    
    # Obtener todas las reservas confirmadas para el mes seleccionado
    reservas = Reserva.objects.filter(
        Q(estado='CONFIRMADA') &
        (
            # Reservas que empiezan en el mes seleccionado
            Q(fecha_inicio__year=anio, fecha_inicio__month=mes) |
            # Reservas indefinidas que empezaron antes y siguen activas
            Q(es_indefinida=True, fecha_inicio__lte=timezone.datetime(anio, mes, 1)) |
            # Reservas temporales que se extienden al mes seleccionado
            Q(
                es_indefinida=False,
                fecha_inicio__lte=timezone.datetime(anio, mes, 1),
                fecha_fin__gte=timezone.datetime(anio, mes, 1)
            )
        )
    ).select_related('casa', 'usuario', 'casa__estilo')
    
    # Generar lista de meses para el selector
    meses = [
        (i, datetime(2000, i, 1).strftime('%B'))
        for i in range(1, 13)
    ]
    
    # Generar lista de años (desde 2023 hasta el año actual + 1)
    anios = range(2023, timezone.now().year + 2)
    
    context = {
        'reservas': reservas,
        'meses': meses,
        'anios': anios,
        'mes_seleccionado': mes,
        'anio_seleccionado': anio
    }
    return render(request, 'properties/reporte_alquileres.html', context)

@login_required
def procesar_pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    # Verificar si la reserva está expirada o si se recibe la señal de expiración
    if reserva.esta_expirada() or (request.method == "POST" and request.headers.get('Content-Type') == 'application/json'):
        # Marcar la casa como disponible
        casa = reserva.casa
        casa.disponible = True
        casa.save()
        
        # Eliminar la reserva en lugar de solo marcarla como cancelada
        reserva.delete()
        
        # Si es una petición AJAX, devolver respuesta JSON
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'status': 'success'})
            
        messages.error(request, "El tiempo para realizar el pago ha expirado")
        return redirect('accounts:profile')
    
    if request.method == "POST":
        if not reserva.tipo_plan:
            tipo_plan = request.POST.get('tipo_plan')
            if tipo_plan not in [choice[0] for choice in Reserva.TIPOS_PLAN]:
                messages.error(request, "Plan de pago inválido")
                return redirect('accounts:profile')
                
            reserva.tipo_plan = tipo_plan
            reserva.cuotas_totales = reserva.calcular_cuotas_totales()
            reserva.fecha_ultimo_pago = timezone.now()
            reserva.save()
            
            messages.success(request, "Plan seleccionado exitosamente. Por favor, realice el primer pago.")
            return redirect('accounts:profile')
        
        # Si ya tiene plan, procesar el pago
        perfil = request.user.perfilusuario
        monto = Decimal(str(reserva.calcular_monto_pago()))
        
        if perfil.saldo >= monto:
            perfil.saldo -= monto
            perfil.save()
            
            reserva.cuotas_pagadas += 1
            reserva.fecha_ultimo_pago = timezone.now()
            
            if reserva.cuotas_pagadas >= reserva.cuotas_totales:
                reserva.estado = 'PAGADA'
            else:
                reserva.estado = 'CONFIRMADA'
            reserva.save()
            
            messages.success(request, f"Pago procesado exitosamente. Cuota {reserva.cuotas_pagadas}/{reserva.cuotas_totales}. Monto pagado: ${monto}")
        else:
            messages.error(request, "Saldo insuficiente para realizar el pago")
    
    return redirect('accounts:profile')