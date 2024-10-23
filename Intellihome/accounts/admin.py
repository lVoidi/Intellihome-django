from django.contrib import admin
from .models import SystemStatus

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
