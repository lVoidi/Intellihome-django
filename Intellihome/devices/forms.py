from django import forms
from .models import DispositivoIoT

class DispositivoIoTForm(forms.ModelForm):
    class Meta:
        model = DispositivoIoT
        fields = ['nombre', 'tipo', 'ubicacion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Termostato Sala'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sala Principal'
            }),
        }