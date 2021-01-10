from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

# Create your models here.


class Genero(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Género', unique=True)

    def __str__(self):
        return self.nombre


class Autor(models.Model):
    nombre = models.CharField(max_length=250, verbose_name='Autor')

    def __str__(self):
        return self.nombre


class Editorial(models.Model):
    nombre = models.CharField(max_length=150, verbose_name='Editorial')

    def __str__(self):
        return self.nombre


class CasaLibro(models.Model):
    url = models.URLField(verbose_name='URL de la Casa del Libro', primary_key=True)
    precio = models.FloatField(verbose_name='Precio')


class Libro(models.Model):
    titulo = models.CharField(max_length=250, verbose_name='Título')
    titulo_original = models.CharField(max_length=250, verbose_name='Título original')
    anyo_publicacion = models.PositiveSmallIntegerField(verbose_name='Año de publicación')
    autor = models.ManyToManyField(Autor)
    genero = models.ForeignKey(Genero, on_delete=models.SET_NULL, null=True)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True)
    sinopsis = models.TextField(verbose_name='Sinopsis', null=True)
    url_imagen = models.URLField(verbose_name='URL de la portada')
    casa_libro = models.OneToOneField(CasaLibro, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo

    def __lt__(self, other):
        return self.id < other.id


class MyUserManager(BaseUserManager):
    def _create_user(self, username, email=None, genre=None, password=None, **extra_fields):

        if not username:
            raise ValueError('The given username must be set')

        genero = Genero.objects.get(pk=genre)

        user = self.model(
            username=self.model.normalize_username(username),
            email=MyUserManager.normalize_email(email),
            genre=genero,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, genre=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, genre, password, **extra_fields)

    def create_superuser(self, username, email, genre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, genre, password, **extra_fields)


class Usuario(AbstractUser):
    genre = models.ForeignKey(Genero, on_delete=models.SET_NULL, null=True)
    saved_books = models.ManyToManyField(Libro)

    REQUIRED_FIELDS = ['email', 'genre']

    objects = MyUserManager()
