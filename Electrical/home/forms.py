from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Appliance

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['monthly_limit', 'season', 'temperature', 'humidity']
        widgets = {
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'humidity': forms.NumberInput(attrs={'step': '0.1'}),
        }

class ApplianceForm(forms.ModelForm):
    class Meta:
        model = Appliance
        fields = ['name', 'power_consumption', 'daily_usage']
        widgets = {
            'power_consumption': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'daily_usage': forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': '24'}),
        } 