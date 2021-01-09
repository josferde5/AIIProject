from django.shortcuts import render, redirect
from .admin import UserCreateForm
from django.contrib.auth import logout as log_out, login as log_in, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test, login_required
import urllib.request
from bs4 import BeautifulSoup
import main.populate as populate
from .forms import BusquedaPorGeneroForm, BusquedaPorEditorialForm, BusquedaPorAnyoPublicacionForm, \
    BusquedaPorAutorForm, BusquedaPorTituloForm, BusquedaAvanzadaForm
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, FuzzyTermPlugin, PhrasePlugin, SequencePlugin, MultifieldParser
from whoosh.query import NumericRange
from .models import Libro

import re


# Create your views here.


def index(request):
    formulario = BusquedaPorTituloForm()
    return render(request, 'index.html', {'formulario': formulario})


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


def standard_search(qp, searcher, search_query):
    libros = []
    q = qp.parse(search_query)
    books = searcher.search(q)
    for book in books:
        libros.append({'titulo': book['titulo'],
                       'titulo_original': book['titulo_original'],
                       'publicacion': book['anyo_publicacion'],
                       'autor': book['autor']})

    return libros


def fuzzy_term_search(qp, searcher, search_query):
    qp.add_plugin(FuzzyTermPlugin())
    qp.remove_plugin_class(PhrasePlugin)
    qp.add_plugin(SequencePlugin())
    q = qp.parse(search_query)
    books = searcher.search(q)

    return books


def numeric_range_search(q, searcher):
    libros = []
    books = searcher.search(q)
    for book in books:
        libros.append({'titulo': book['titulo'],
                       'titulo_original': book['titulo_original'],
                       'publicacion': book['anyo_publicacion'],
                       'autor': book['autor']})

    return libros


# TODO: Paginación


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
                    libros.append({'id_libro': book['id'],
                                   'titulo': book['titulo'],
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
                    libros.append({'id_libro': book['id'],
                                   'titulo': book['titulo'],
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
                    libros.append({'id_libro': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporanyopublicacion.html', {'formulario': formulario, 'libros': libros})


def buscar_por_autor(request):
    formulario = BusquedaPorAutorForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaPorAutorForm(request.POST)
        if formulario.is_valid():
            autor = str(formulario.cleaned_data.get('author'))
            author_sp = autor.split()

            search_query = ''
            for s in author_sp:
                search_query = search_query + s + "~2 "

            search_query = u'"' + search_query.strip() + '"~2'
            ix = open_dir(populate.whoosh_dir)

            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser('autor', ix.schema)
                qp.add_plugin(FuzzyTermPlugin())
                qp.remove_plugin_class(PhrasePlugin)
                qp.add_plugin(SequencePlugin())
                q = qp.parse(search_query)
                books = searcher.search(q)

                for book in books:
                    libros.append({'id_libro': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporautor.html', {'formulario': formulario, 'libros': libros})


def buscar_por_titulo(request):
    formulario = BusquedaPorTituloForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaPorTituloForm(request.POST)
        if formulario.is_valid():
            titulo = str(formulario.cleaned_data.get('title'))
            titulo_sp = titulo.split()

            search_query = ''
            for s in titulo_sp:
                search_query = search_query + s + "~2 "

            search_query = u'"' + search_query.strip() + '"~2'
            ix = open_dir(populate.whoosh_dir)

            libros = []
            with ix.searcher() as searcher:
                qp = MultifieldParser(['titulo', 'titulo_original'], schema=ix.schema)
                # qp.add_plugin(FuzzyTermPlugin())
                # qp.remove_plugin_class(PhrasePlugin)
                # qp.add_plugin(SequencePlugin())
                # q = qp.parse(search_query)
                books = fuzzy_term_search(qp, searcher, search_query)

                for book in books:
                    libros.append({'id_libro': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaportitulo.html', {'formulario': formulario, 'libros': libros})


def busqueda_avanzada(request):
    formulario = BusquedaAvanzadaForm()
    libros = None

    if request.method == 'POST':
        formulario = BusquedaAvanzadaForm(request.POST)
        if formulario.is_valid():
            title = str(formulario.cleaned_data.get('title'))
            author = str(formulario.cleaned_data.get('author'))
            start = formulario.cleaned_data.get('start')
            end = formulario.cleaned_data.get('end')
            publisher = formulario.cleaned_data.get('publisher')
            genre = formulario.cleaned_data.get('genre')

            libros = []

            if title or author or start or end or publisher or genre:

                ix = open_dir(populate.whoosh_dir)

                with ix.searcher() as searcher:
                    docnums = set()

                    if not title:
                        for docnum in searcher.document_numbers():
                            docnums.add(docnum)
                    else:
                        title_sp = title.split()
                        author_search_query = ''
                        for s in title_sp:
                            author_search_query = author_search_query + s + "~2 "
                        author_search_query = u'"' + author_search_query.strip() + '"~2'
                        qp = MultifieldParser(['titulo', 'titulo_original'], schema=ix.schema)
                        # qp.add_plugin(FuzzyTermPlugin())
                        # qp.remove_plugin_class(PhrasePlugin)
                        # qp.add_plugin(SequencePlugin())
                        # q = qp.parse(author_search_query)
                        books = fuzzy_term_search(qp, searcher, author_search_query)

                        for result in books:
                            docnums.add(result.docnum)

                    if author and len(docnums) > 0:
                        author_sp = author.split()
                        author_search_query = ''
                        for s in author_sp:
                            author_search_query = author_search_query + s + "~2 "
                        author_search_query = u'"' + author_search_query.strip() + '"~2'
                        qp = QueryParser('autor', ix.schema)
                        qp.add_plugin(FuzzyTermPlugin())
                        qp.remove_plugin_class(PhrasePlugin)
                        qp.add_plugin(SequencePlugin())
                        q = qp.parse(author_search_query)
                        books = searcher.search(q, filter=docnums)
                        docnums = set()
                        for result in books:
                            docnums.add(result.docnum)

                    if start and end and len(docnums) > 0:
                        q = NumericRange('anyo_publicacion', start, end)
                        books = searcher.search(q, filter=docnums)
                        docnums = set()
                        for result in books:
                            docnums.add(result.docnum)

                    if publisher and len(docnums) > 0:
                        qp = QueryParser("editorial", schema=ix.schema)
                        q = qp.parse(publisher.nombre)
                        books = searcher.search(q)
                        docnums = set()
                        for result in books:
                            docnums.add(result.docnum)

                    if genre and len(docnums) > 0:
                        qp = QueryParser("genero", schema=ix.schema)
                        q = qp.parse(genre.nombre)
                        books = searcher.search(q, filter=docnums)

                    for book in books:
                        libros.append({'id_libro': book['id'],
                                       'titulo': book['titulo'],
                                       'titulo_original': book['titulo_original'],
                                       'publicacion': book['anyo_publicacion'],
                                       'autor': book['autor']})

    return render(request, 'busquedaavanzada.html', {'formulario': formulario, 'libros': libros})


def vista_libro(request, id_libro):
    libro = Libro.objects.get(pk=id_libro)
    return render(request, 'libro.html', {'libro': libro})


@login_required
def libros_guardados(request):
    # TODO: Funcionalidad para guardar libros
    pass


@login_required
def recomendaciones_usuario(request):
    # TODO: Sistemas de recomendación
    pass


def get_books_from(url):
    # TODO: Mejorar BS (sinopsis, url_imagen), hacer BS en Casa del Libro y página de reviews
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
        synopsis_p = s.find('div', class_='profile__text')
        if synopsis_p is not None and synopsis_p.div.p is None:
            synopsis = ''.join(s.find('div', class_='profile__text').div.find(text=True, recursive=False).strip())
        elif synopsis_p is not None:
            synopsis = synopsis_p.text.strip()
        else:
            synopsis = None

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
