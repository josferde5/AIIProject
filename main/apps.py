from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        from .models import Genero
        Genero.objects.get_or_create(nombre='Prueba')
