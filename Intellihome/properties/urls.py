from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('configuracion/', views.configuracion_admin, name='configuracion'),
    path('agregar-casa/', views.agregar_casa, name='agregar_casa'),
    path('casas/', views.lista_casas, name='lista_casas'),
    path('casas/<int:casa_id>/', views.detalle_casa, name='detalle_casa'),
    path('casas/<int:casa_id>/eliminar/', views.eliminar_casa, name='eliminar_casa'),
]
