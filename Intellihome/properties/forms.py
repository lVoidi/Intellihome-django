from django import forms
from .models import Casa, FotoCasa, ConfiguracionFotos

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
