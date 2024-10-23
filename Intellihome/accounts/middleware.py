from django.shortcuts import render
from .models import SystemStatus

class SystemStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin/'):
            try:
                system_status = SystemStatus.objects.first()
                if system_status and not system_status.is_enabled:
                    return render(request, 'accounts/system_disabled.html', {
                        'message': system_status.disabled_message
                    })
            except SystemStatus.DoesNotExist:
                pass
        return self.get_response(request)