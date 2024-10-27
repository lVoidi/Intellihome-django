from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .forms import CasaForm, RangoFechasForm
from .models import FotoCasa, Casa, Reserva, ConfiguracionTiempoSimulado
from datetime import datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from decimal import Decimal


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
        
        # Obtener las reservas que se solapan con el rango seleccionado
        reservas = Reserva.objects.filter(
            Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio)
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
        es_indefinida = request.POST.get('es_indefinida') == 'on'
        fecha_inicio = request.POST.get('fecha_inicio')
        
        if es_indefinida:
            fecha_fin = timezone.now().date() + timezone.timedelta(days=365)  # Un año por defecto
        else:
            fecha_fin = request.POST.get('fecha_fin')

        # Verificar si ya existe una reserva válida para estas fechas
        reservas_existentes = Reserva.objects.filter(
            casa=casa,
            estado__in=['TEMPORAL', 'CONFIRMADA']
        ).filter(
            Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio)
        ).exclude(
            estado='TEMPORAL',
            fecha_reserva__lt=timezone.now() - timezone.timedelta(minutes=5)
        )

        if reservas_existentes.exists():
            messages.error(request, "La casa no está disponible para las fechas seleccionadas")
            return redirect('properties:detalle_casa', casa_id=casa_id)

        # Crear la reserva temporal
        reserva = Reserva.objects.create(
            casa=casa,
            usuario=request.user,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            es_indefinida=es_indefinida,
            estado='TEMPORAL'
        )

        return redirect('properties:confirmar_pago', reserva_id=reserva.id)

    return render(request, 'properties/reservar_casa.html', {
        'casa': casa,
        'form': RangoFechasForm()
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
def confirmar_pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    # Obtener o crear la configuración de tiempo
    config_tiempo, created = ConfiguracionTiempoSimulado.objects.get_or_create(
        defaults={'minutos_reserva_temporal': 15}
    )
    
    # Calcular el costo total
    if reserva.es_indefinida:
        costo_total = reserva.casa.monto
    else:
        dias = (reserva.fecha_fin - reserva.fecha_inicio).days
        costo_total = reserva.casa.monto_diario * dias
    
    if request.method == "POST":
        # Debug logs
        print(f"Usuario: {request.user.username}")
        print(f"Tiene método de pago principal: {request.user.perfilusuario.metodos_pago.filter(es_principal=True).exists()}")
        print(f"Estado actual de la reserva: {reserva.estado}")
        
        # Verificar que el usuario tenga un método de pago
        if not request.user.perfilusuario.metodos_pago.filter(es_principal=True).exists():
            messages.error(request, "Necesitas tener un método de pago principal para continuar")
            return redirect('accounts:user_home')
        
        try:
            # Actualizar la reserva
            reserva.estado = 'CONFIRMADA'
            reserva.fecha_reserva = timezone.now()
            reserva.proximo_pago = reserva.fecha_inicio + timezone.timedelta(days=30)
            reserva.save()
            
            # Debug log
            print(f"Nuevo estado de la reserva: {reserva.estado}")
            
            messages.success(
                request, 
                f"¡Reserva confirmada exitosamente! El pago de ${costo_total:.2f} ha sido procesado."
            )
            return redirect('accounts:profile')  # Cambiamos aquí
            
        except Exception as e:
            messages.error(request, "Hubo un error al procesar el pago. Por favor, intenta nuevamente.")
            return redirect('properties:lista_casas')
    
    context = {
        'reserva': reserva,
        'tiempo_restante': config_tiempo.minutos_reserva_temporal,
        'costo_total': costo_total
    }
    
    return render(request, 'properties/confirmar_pago.html', context)


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
def procesar_pago(request, reserva_id):
    if request.method == "POST":
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        perfil = request.user.perfilusuario
        tipo_pago = request.POST.get('tipo_pago', 'completo')
        
        # Calcular monto total y cuotas
        monto_total = reserva.casa.monto if reserva.es_indefinida else reserva.casa.monto_diario
        
        if tipo_pago == 'semanal':
            dias_extension = 7
            monto = monto_total / 4
            cuotas_totales = 4
        elif tipo_pago == 'diario':
            dias_extension = 1
            monto = monto_total / 30
            cuotas_totales = 30
        else:  # pago completo
            dias_extension = 30
            monto = monto_total
            cuotas_totales = 1
        
        if perfil.saldo < monto:
            messages.error(request, "Saldo insuficiente")
            return redirect('accounts:profile')
        
        try:
            # Descontar saldo
            perfil.saldo -= Decimal(str(monto))
            perfil.save()
            
            # Actualizar reserva
            reserva.tipo_pago_actual = tipo_pago.upper()
            reserva.cuotas_totales = cuotas_totales
            reserva.cuotas_pagadas += 1
            
            # Registrar el pago en el historial
            pago = {
                'fecha': timezone.now().isoformat(),
                'monto': float(monto),
                'tipo_pago': tipo_pago,
                'cuota_numero': reserva.cuotas_pagadas
            }
            historial = reserva.historial_pagos
            historial.append(pago)
            reserva.historial_pagos = historial
            
            # Actualizar próximo pago
            reserva.proximo_pago = timezone.now().date() + timezone.timedelta(days=dias_extension)
            reserva.save()
            
            # Actualizar tiempo restante
            dias_extension_simulados = dias_extension / 6  # 30 días = 5 minutos
            reserva.tiempo_restante_minutos = dias_extension_simulados
            
            messages.success(
                request, 
                f"Pago de ${monto:.2f} procesado exitosamente. "
                f"Cuota {reserva.cuotas_pagadas}/{cuotas_totales} pagada. "
                f"Próximo pago en {dias_extension} días."
            )
            
        except Exception as e:
            messages.error(request, "Error al procesar el pago")
            print(f"Error en procesar_pago: {str(e)}")
            
        return redirect('accounts:profile')
    
    return redirect('accounts:profile')

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
