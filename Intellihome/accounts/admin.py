from django.contrib import admin
from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from django.urls import path
from .models import SystemStatus, EstiloCasa, TipoTransporte, PerfilUsuario, PromocionAdministrador
from .utils import enviar_mensaje
import random
import string

# Register your models here.

@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ('is_enabled', 'modified_by', 'last_modified')
    readonly_fields = ('modified_by', 'last_modified')
    
    def save_model(self, request, obj, form, change):
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Solo permite crear una instancia
        return not SystemStatus.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # No permite eliminar la configuración
        return False

@admin.register(EstiloCasa)
class EstiloCasaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(TipoTransporte)
class TipoTransporteAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_verificado', 'fecha_nacimiento', 'foto_perfil_preview', 'promocion_admin')
    list_filter = ('email_verificado', 'incluir_pago')
    readonly_fields = ('foto_perfil_preview',)
    actions = ['promover_a_administrador', 'revocar_administrador']

    def foto_perfil_preview(self, obj):
        if obj.foto_perfil:
            return mark_safe(f'<img src="{obj.foto_perfil.url}" width="100" />')
        return "Sin foto"
    
    foto_perfil_preview.short_description = 'Vista previa de foto'

    def promocion_admin(self, obj):
        if obj.user.is_superuser:
            return 'Administrador Principal'
            
        try:
            promocion = PromocionAdministrador.objects.filter(
                usuario=obj.user
            ).latest('fecha_solicitud')
            
            if promocion.estado == 'pendiente':
                return 'Pendiente'
            elif promocion.estado == 'aceptada':
                return 'Administrador Promovido'
            elif promocion.codigo_confirmacion == 'REVOKED':
                return 'Revocado'
            else:
                return 'Rechazada'
        except PromocionAdministrador.DoesNotExist:
            if obj.user.is_staff:
                return 'Administrador Promovido'
            return 'Usuario normal'

    def promover_a_administrador(self, request, queryset):
        for perfil in queryset:
            if not perfil.user.is_staff:
                codigo = ''.join(random.choices(string.digits, k=6))
                PromocionAdministrador.objects.create(
                    usuario=perfil.user,
                    codigo_confirmacion=codigo
                )
                mensaje = f"""
                Has sido seleccionado para ser promovido a administrador.
                
                Para confirmar o rechazar esta promoción, por favor visita:
                http://{request.get_host()}/accounts/confirmar-promocion/{codigo}/
                
                """
                enviar_mensaje(perfil.user.email, mensaje)
        self.message_user(request, "Se han enviado las invitaciones de promoción")
    
    promover_a_administrador.short_description = "Promover a administrador"

    def revocar_administrador(self, request, queryset):
        for perfil in queryset:
            if perfil.user.is_staff and not perfil.user.is_superuser:
                usuario = perfil.user
                usuario.is_staff = False
                usuario.save()
                
                # Registrar la revocación
                PromocionAdministrador.objects.create(
                    usuario=usuario,
                    estado='rechazada',
                    codigo_confirmacion='REVOKED'
                )
                
                # Enviar notificación al usuario
                mensaje = """
                Tu rol de administrador ha sido revocado por el administrador principal.
                
                Si tienes alguna pregunta, por favor contacta al administrador del sistema.
                """
                enviar_mensaje(usuario.email, None, message=mensaje)
        
        self.message_user(request, "Se han revocado los permisos de administrador seleccionados")
    
    revocar_administrador.short_description = "Revocar permisos de administrador"
