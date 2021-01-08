from django import forms
from .models import Genero, Editorial


class BusquedaPorGeneroForm(forms.Form):
    genre = forms.ModelChoiceField(queryset=Genero.objects.all())


class BusquedaPorEditorialForm(forms.Form):
    publisher = forms.ModelChoiceField(queryset=Editorial.objects.all())


class BusquedaPorAnyoPublicacionForm(forms.Form):
    start = forms.IntegerField(label="Buscar desde:")
    end = forms.IntegerField(label="Buscar hasta:")
