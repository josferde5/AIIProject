from django.shortcuts import render, redirect
from .admin import UserCreateForm
from django.contrib.auth import logout as log_out, login as log_in, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
import urllib.request
from bs4 import BeautifulSoup
import main.populate as populate
from .forms import BusquedaPorGeneroForm, BusquedaPorEditorialForm, BusquedaPorAnyoPublicacionForm
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.query import NumericRange
from .models import Genero

import re


# Create your views here.


def index(request):
    return render(request, 'index.html')


def register(request):
    form = UserCreateForm()
    if request.method == 'POST':
        form = UserCreateForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            if user is not None:
                log_in(request, user)
                return redirect('/')

    return render(request, 'register.html', {'formulario': form})


def login(request):
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                log_in(request, user)
                return redirect('/')

    return render(request, 'login.html', {'formulario': form})


def logout(request):
    log_out(request)
    return redirect('/')


def buscar_por_genero(request):
    formulario = BusquedaPorGeneroForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaPorGeneroForm(request.POST)
        if formulario.is_valid():
            genre = formulario.cleaned_data.get('genre')
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser("genero", schema=ix.schema)
                q = qp.parse(genre.nombre)
                books = searcher.search(q)
                for book in books:
                    libros.append({'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporgenero.html', {'formulario': formulario, 'libros': libros})


def buscar_por_editorial(request):
    formulario = BusquedaPorEditorialForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaPorEditorialForm(request.POST)
        if formulario.is_valid():
            publisher = formulario.cleaned_data.get('publisher')
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser("editorial", schema=ix.schema)
                q = qp.parse(publisher.nombre)
                books = searcher.search(q)
                for book in books:
                    libros.append({'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporeditorial.html', {'formulario': formulario, 'libros': libros})


def buscar_por_anyo_publicacion(request):
    formulario = BusquedaPorAnyoPublicacionForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaPorAnyoPublicacionForm(request.POST)
        if formulario.is_valid():
            start = formulario.cleaned_data.get('start')
            end = formulario.cleaned_data.get('end')
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                q = NumericRange('anyo_publicacion', start, end)
                books = searcher.search(q)
                for book in books:
                    libros.append({'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporanyopublicacion.html', {'formulario': formulario, 'libros': libros})


def get_books_from(url):
    l = []
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f, "lxml")
    books = s.find('div', class_='datalist datalist--img').find('ul').find_all('li')
    for book in books:
        year_before = book.find('p').find('span', class_='date').string.strip()
        year = re.sub('\(.*\)', '', year_before)
        book_title_url = book.find_all('a')[0]
        title = ''.join(book_title_url.stripped_strings)
        original_title = title
        book_url = book_title_url['href']
        author = ''.join(book.find_all('a')[1].stripped_strings)

        f = urllib.request.urlopen(book_url)
        s = BeautifulSoup(f, "lxml")
        book_info = s.find('div', class_='profile__data').find('ul').find_all('li')
        genre = None
        publisher = None
        for li in book_info:
            li_title = ''.join(li.p.strong.stripped_strings)
            if li_title == 'Título original:':
                original_title = ''.join(li.p.find(text=True, recursive=False).strip())
            if li_title == 'Editorial:':
                publisher_a = li.p.a
                if publisher_a is not None:
                    publisher = ''.join(publisher_a.stripped_strings)
                else:
                    publisher = li.p.find(text=True, recursive=False).strip()
            if li_title == 'Temas:':
                genre = ''.join(li.p.a.stripped_strings)
        synopsis_p = s.find('div', class_='profile__text').div.p
        if synopsis_p is None:
            synopsis = ''.join(s.find('div', class_='profile__text').div.find(text=True, recursive=False).strip())
        else:
            synopsis = synopsis_p.text.strip()

        data = (title, original_title, year, author, genre, publisher, synopsis)
        l.append(data)
    return l


def get_books():
    l = []
    f = urllib.request.urlopen('http://www.lecturalia.com/libros/ac/ultimos-actualizados')
    s = BeautifulSoup(f, "lxml")

    pagination_links = s.find('div', class_='pagination').find('div', class_='pages').find_all('a')
    total_pages = int(pagination_links[len(pagination_links) - 1].string.strip())

    # for i in range(1, 2):
    books = get_books_from('http://www.lecturalia.com/libros/ac/ultimos-actualizados/')  # + str(i))
    l.extend(books)
    return l


@user_passes_test(lambda u: u.is_superuser, login_url="/")
def populate_app(request):
    books = get_books()
    populate.populate_system(books)
    return redirect('/')
