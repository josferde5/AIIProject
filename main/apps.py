from django.apps import AppConfig
import nltk


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        nltk.download('stopwords')

        from .models import Genero
        from .recommendations import deserialize_rs_json
        if len(Genero.objects.all()) == 0:
            Genero.objects.create(nombre='Prueba').save()
        deserialize_rs_json()
