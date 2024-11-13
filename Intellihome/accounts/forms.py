from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
import random
import string
from .models import PerfilUsuario, EstiloCasa, TipoTransporte
from .utils import enviar_mensaje

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label='Nombre')
    last_name = forms.CharField(required=True, label='Apellido')
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de nacimiento'
    )
    foto_perfil = forms.ImageField(required=False)
    incluir_pago = forms.BooleanField(required=False, label='¿Desea incluir forma de pago?')
    estilos_casa = forms.ModelMultipleChoiceField(
        queryset=EstiloCasa.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    tipos_transporte = forms.ModelMultipleChoiceField(
        queryset=TipoTransporte.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                 'fecha_nacimiento', 'foto_perfil', 'incluir_pago', 'estilos_casa', 'tipos_transporte')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            codigo = ''.join(random.choices(string.digits, k=6))
            perfil = PerfilUsuario.objects.create(
                user=user,
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                foto_perfil=self.cleaned_data.get('foto_perfil'),
                incluir_pago=self.cleaned_data['incluir_pago'],
                codigo_verificacion=codigo
            )
            perfil.estilos_casa.set(self.cleaned_data['estilos_casa'])
            perfil.tipos_transporte.set(self.cleaned_data['tipos_transporte'])
            
            enviar_mensaje(user.email, codigo)
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': 'Por favor, introduzca un nombre de usuario y clave correctos o el usuario esta inhabilitado.',
        'inactive': 'Este usuario está inhabilitado. Por favor, contacte al administrador.',
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                if not self.user_cache.is_active:
                    raise ValidationError(
                        self.error_messages['inactive'],
                        code='inactive',
                    )
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class VerificationCodeForm(forms.Form):
    codigo = forms.CharField(max_length=6, min_length=6, label='Código de verificación')

class SetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='''La contraseña debe tener:
        • Mínimo 7 caracteres
        • Al menos una mayúscula
        • Al menos un símbolo especial
        • Al menos un número
        • Al menos una minúscula'''
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput
    )

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 7:
            raise ValidationError('La contraseña debe tener al menos 7 caracteres.')
        
        if not any(c.isupper() for c in password):
            raise ValidationError('La contraseña debe contener al menos una mayúscula.')
        
        if not any(c.islower() for c in password):
            raise ValidationError('La contraseña debe contener al menos una minúscula.')
        
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        if not any(not c.isalnum() for c in password):
            raise ValidationError('La contraseña debe contener al menos un símbolo especial.')
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden')
        return cleaned_data

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            return email
        except User.DoesNotExist:
            # No indicamos si el correo existe o no
            return email

class UserProfileEditForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label='Nombre')
    last_name = forms.CharField(required=True, label='Apellido')
    username = forms.CharField(required=True, label='Usuario (alias)')
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de nacimiento'
    )
    foto_perfil = forms.ImageField(required=False)
    incluir_pago = forms.BooleanField(required=False, label='¿Desea incluir forma de pago?')
    estilos_casa = forms.ModelMultipleChoiceField(
        queryset=EstiloCasa.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    tipos_transporte = forms.ModelMultipleChoiceField(
        queryset=TipoTransporte.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = PerfilUsuario
        fields = ('username', 'first_name', 'last_name', 'email',
                 'fecha_nacimiento', 'foto_perfil', 'incluir_pago', 'estilos_casa', 'tipos_transporte')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(id=self.instance.user.id).filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(id=self.instance.user.id).filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

class PaymentInfoForm(forms.Form):
    nombre_tarjetahabiente = forms.CharField(required=True, label='Nombre del Tarjetahabiente')
    numero_tarjeta = forms.CharField(
        required=True, 
        max_length=16, 
        min_length=16, 
        label='Número de Tarjeta',
        widget=forms.TextInput(attrs={'pattern': '[0-9]*'})
    )
    fecha_validez = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de Validez'
    )
    numero_verificador = forms.CharField(
        required=True, 
        max_length=4, 
        min_length=4, 
        label='Número Verificador',
        widget=forms.TextInput(attrs={'pattern': '[0-9]*'})
    )

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data['numero_tarjeta']
        if not numero.isdigit():
            raise ValidationError('El número de tarjeta debe contener solo dígitos')
        
        primer_digito = numero[0]
        marcas_validas = {'1': 'Visca', '2': 'MasterChef', '3': 'AmericanCity', '5': 'TicaPay'}
        
        if primer_digito not in marcas_validas:
            raise ValidationError('Número de tarjeta inválido. El primer dígito debe ser 1, 2, 3 o 5')
        
        self.marca_tarjeta = marcas_validas[primer_digito]
        return numero
