from datetime import timezone
from django import forms
from django.utils import timezone  # Cambiado aquí
from .models import Casa, FotoCasa, ConfiguracionFotos
from accounts.models import EstiloCasa as Estilo  # Cambiado aquí

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class CasaForm(forms.ModelForm):
    latitud = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': 'Ej: 9.928100'
        }),
        help_text='Ingrese la latitud o seleccione en el mapa'
    )
    longitud = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': 'Ej: -84.090700'
        }),
        help_text='Ingrese la longitud o seleccione en el mapa'
    )
    fotos = MultipleFileField(
        required=True,
        help_text='Seleccione al menos 3 fotografías de la casa'
    )
    amenidades = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Ingrese las amenidades separadas por comas (ej: Piscina, Gimnasio, WiFi)'
    )
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1000.00'
        }),
        help_text='Digite el monto mensual, este monto contempla los servicios'
    )

    class Meta:
        model = Casa
        fields = ['estilo', 'capacidad', 'habitaciones', 'banos', 
                 'amenidades', 'caracteristicas', 'latitud', 'longitud', 'monto']

    def clean_fotos(self):
        fotos = self.files.getlist('fotos')
        config = ConfiguracionFotos.objects.first()
        min_fotos = 3  # valor por defecto
        
        if config:
            min_fotos = config.cantidad_minima
            
        if len(fotos) < min_fotos:
            raise forms.ValidationError(
                f'Debe subir al menos {min_fotos} fotografías'
            )
        return fotos

class RangoFechasForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de inicio'
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de fin'
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio < timezone.now().date():
                raise forms.ValidationError('La fecha de inicio no puede ser anterior a hoy')
            
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')

        return cleaned_data
