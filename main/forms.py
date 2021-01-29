from django import forms
from .models import Genero, Editorial


class BusquedaPorGeneroForm(forms.Form):
    genre = forms.ModelChoiceField(queryset=Genero.objects.all())
    page = forms.IntegerField(required=False)


class BusquedaPorEditorialForm(forms.Form):
    publisher = forms.ModelChoiceField(queryset=Editorial.objects.all())
    page = forms.IntegerField(required=False)


class BusquedaPorAnyoPublicacionForm(forms.Form):
    start = forms.IntegerField(label="Buscar desde:")
    end = forms.IntegerField(label="Buscar hasta:")
    page = forms.IntegerField(required=False)

    def clean(self):
        super(BusquedaPorAnyoPublicacionForm, self)
        start_val = self.cleaned_data.get('start')
        end_val = self.cleaned_data.get('end')

        if end_val < start_val:
            self._errors['start'] = self.error_class(['El año de inicio no puede ser posterior al año de fin'])
            self._errors['end'] = self.error_class(['El año de inicio no puede ser posterior al año de fin'])

            return self.cleaned_data


class BusquedaPorAutorForm(forms.Form):
    author = forms.CharField(label='Autor:')
    page = forms.IntegerField(required=False)


class BusquedaPorTituloForm(forms.Form):
    title = forms.CharField(label='Título:')
    page = forms.IntegerField(required=False)


class BusquedaAvanzadaForm(forms.Form):
    title = forms.CharField(label='Título:', required=False)
    author = forms.CharField(label='Autor:', required=False)
    start = forms.IntegerField(label="Buscar desde:", required=False)
    end = forms.IntegerField(label="Buscar hasta:", required=False)
    genre = forms.ModelChoiceField(queryset=Genero.objects.all(), required=False)
    publisher = forms.ModelChoiceField(queryset=Editorial.objects.all(), required=False)

    def clean(self):
        super(BusquedaAvanzadaForm, self)
        start_val = self.cleaned_data.get('start')
        end_val = self.cleaned_data.get('end')
        if start_val and not end_val:
            self._errors['end'] = self.error_class(
                ['Si se especifica una fecha de inicio, se debe especificar una fecha de fin'])
        if end_val and not start_val:
            self._errors['start'] = self.error_class(
                ['Si se especifica una fecha de fin, se debe especificar una fecha de inicio'])
        if end_val and start_val and end_val < start_val:
            self._errors['start'] = self.error_class(['El año de inicio no puede ser posterior al año de fin'])
            self._errors['end'] = self.error_class(['El año de inicio no puede ser posterior al año de fin'])

            return self.cleaned_data
