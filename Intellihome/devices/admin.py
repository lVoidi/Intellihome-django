from django.contrib import admin
from .models import TipoDispositivo, DispositivoIoT

@admin.register(TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(DispositivoIoT)
class DispositivoIoTAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'ubicacion', 'casa', 'estado')
    list_filter = ('tipo', 'estado', 'casa')
    search_fields = ('nombre', 'ubicacion')