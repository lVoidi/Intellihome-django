from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import SystemStatus, AdminPasswordStatus

class SystemStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin'):
            try:
                system_status = SystemStatus.objects.first()
                if system_status and not system_status.is_enabled:
                    return render(request, 'accounts/system_disabled.html', {
                        'message': system_status.disabled_message
                    })
            except SystemStatus.DoesNotExist:
                pass
        return self.get_response(request)


class AdminPasswordCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            if request.path.startswith('/admin/'):
                try:
                    password_status = AdminPasswordStatus.objects.get(user=request.user)
                    time_diff = timezone.now() - password_status.last_password_change
                    if time_diff > timedelta(minutes=2):
                        messages.warning(
                            request,
                            'Por favor, cambie su contraseña por seguridad.'
                        )
                        if not request.path.endswith('/password_change/'):
                            return redirect('admin:password_change')
                except AdminPasswordStatus.DoesNotExist:
                    AdminPasswordStatus.objects.create(user=request.user)

        return self.get_response(request)