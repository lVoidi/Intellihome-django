from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.lista_casas_disponibles, name='casas_disponibles'),
    path('casas-disponibles/', views.lista_casas_disponibles, name='casas_disponibles_alt'),
    path('configuracion/', views.configuracion_admin, name='configuracion'),
    path('casa/agregar/', views.agregar_casa, name='agregar_casa'),
    path('casas/', views.lista_casas, name='lista_casas'),
    path('casa/<int:casa_id>/', views.detalle_casa, name='detalle_casa'),
    path('casa/<int:casa_id>/eliminar/', views.eliminar_casa, name='eliminar_casa'),
    path('disponibilidad/', views.gestionar_disponibilidad, name='gestionar_disponibilidad'),
    path('casa/<int:casa_id>/disponibilidad/', views.cambiar_disponibilidad, name='cambiar_disponibilidad'),
    path('casa/<int:casa_id>/reservar/', views.reservar_casa, name='reservar_casa'),
    path('reserva/<int:reserva_id>/confirmar-pago/', views.confirmar_pago, name='confirmar_pago'),
    path('casa/<int:casa_id>/inquilinos/', views.ver_inquilinos, name='ver_inquilinos'),
    path('reserva/<int:reserva_id>/procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('reporte-alquileres/', views.reporte_alquileres, name='reporte_alquileres'),
]
