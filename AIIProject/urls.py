"""AIIProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import main.views as views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('index/', views.index),
    path('login/', views.login),
    path('logout/', views.logout),
    path('register/', views.register),
    path('populate/', views.populate_app),
    path('generos/', views.buscar_por_genero),
    path('editoriales/', views.buscar_por_editorial),
    path('fechapublicacion/', views.buscar_por_anyo_publicacion),
    path('autores/', views.buscar_por_autor),
    path('titulos/', views.buscar_por_titulo),
    path('libro/<int:id_libro>', views.vista_libro),
    path('busqueda_avanzada/', views.busqueda_avanzada),
    path('guardados/', views.libros_guardados),
    path('populate_recommendation_dict/', views.populate_recommendation_dict),
    path('recomendaciones/', views.recomendaciones_usuario),
]
