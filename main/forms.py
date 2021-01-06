from django import forms
from .models import Genero


class BusquedaPorGeneroForm(forms.Form):
    genre = forms.ModelChoiceField(queryset=Genero.objects.all())
