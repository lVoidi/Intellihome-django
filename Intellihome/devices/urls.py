from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('casas/', views.lista_casas_dispositivos, name='lista_casas_dispositivos'),
    path('casa/<int:casa_id>/dispositivos/', views.gestionar_dispositivos, name='gestionar_dispositivos'),
    path('dispositivo/<int:dispositivo_id>/cambiar-estado/', views.cambiar_estado, name='cambiar_estado'),
    path('dispositivo/<int:dispositivo_id>/eliminar/', views.eliminar_dispositivo, name='eliminar_dispositivo'),
    path('mis-dispositivos/', views.mis_dispositivos, name='mis_dispositivos'),
    path('probar/<int:dispositivo_id>/', views.probar_dispositivo, name='probar_dispositivo'),
]
