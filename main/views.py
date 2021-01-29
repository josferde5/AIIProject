from django.shortcuts import render, redirect
from .admin import UserCreateForm
from django.contrib.auth import logout as log_out, login as log_in, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import main.populate as populate
from .forms import BusquedaPorGeneroForm, BusquedaPorEditorialForm, BusquedaPorAnyoPublicacionForm, \
    BusquedaPorAutorForm, BusquedaPorTituloForm, BusquedaAvanzadaForm
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, FuzzyTermPlugin, PhrasePlugin, SequencePlugin, MultifieldParser
from whoosh.query import NumericRange
from .models import Libro
from .recommendations import calculate_similar_items, ItemFilteringDictionary, get_recommended_items_for_user, \
    get_related_items_for_book, serialize_rs_json
import re
import logging

# Create your views here.


logger = logging.getLogger(__name__)


def index(request):
    formulario = BusquedaPorTituloForm()
    recomendados = None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)
    return render(request, 'index.html', {'formulario': formulario, 'recomendados': recomendados})


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


def fuzzy_term_search(qp, searcher, search_query, page):
    qp.add_plugin(FuzzyTermPlugin())
    qp.remove_plugin_class(PhrasePlugin)
    qp.add_plugin(SequencePlugin())
    q = qp.parse(search_query)
    if page:
        books = searcher.search_page(q, page)
    else:
        books = searcher.search(q)

    return books


def calculate_pagination(page, pagecount):
    lowest_page_shown = page - 5 if page - 5 > 1 else 2
    highest_page_shown = page + 5 if page + 5 < pagecount else pagecount
    range_loop = range(lowest_page_shown, highest_page_shown) if highest_page_shown >= lowest_page_shown else None

    return range_loop, page - 5 > 1, page + 5 < pagecount


def buscar_por_genero(request):
    formulario = BusquedaPorGeneroForm()
    libros = None
    recomendados = None
    pagecount, range_loop, space_after_first, space_before_last, page, genre_id = None, None, None, None, None, None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

    if request.method == 'POST':
        formulario = BusquedaPorGeneroForm(request.POST)
        if formulario.is_valid():
            genre = formulario.cleaned_data.get('genre')
            genre_id = genre.id
            page = formulario.cleaned_data.get('page')
            if page is None:
                page = 1
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser("genero", schema=ix.schema)
                q = qp.parse(genre.nombre)
                books = searcher.search_page(q, page)
                pagecount = books.pagecount
                page = pagecount if page > pagecount else page
                range_loop, space_after_first, space_before_last = calculate_pagination(page, books.pagecount)
                for book in books:
                    libros.append({'id': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'anyo_publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporgenero.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados,
                   'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': pagecount,
                   'page': page, 'query_key': 'genre', 'query_value': genre_id})


def buscar_por_editorial(request):
    formulario = BusquedaPorEditorialForm()
    libros = None
    recomendados = None
    pagecount, range_loop, space_after_first, space_before_last, page, publisher_id = None, None, None, None, None, None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

    if request.method == 'POST':
        formulario = BusquedaPorEditorialForm(request.POST)
        if formulario.is_valid():
            publisher = formulario.cleaned_data.get('publisher')
            publisher_id = publisher.id
            page = formulario.cleaned_data.get('page')
            if page is None:
                page = 1
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser("editorial", schema=ix.schema)
                q = qp.parse(publisher.nombre)
                books = searcher.search_page(q, page)
                pagecount = books.pagecount
                page = pagecount if page > pagecount else page
                range_loop, space_after_first, space_before_last = calculate_pagination(page, books.pagecount)
                for book in books:
                    libros.append({'id': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'anyo_publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporeditorial.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados,
                   'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': pagecount,
                   'page': page, 'query_key': 'publisher', 'query_value': publisher_id})


def buscar_por_anyo_publicacion(request):
    formulario = BusquedaPorAnyoPublicacionForm()
    libros = None
    recomendados = None
    pagecount, range_loop, space_after_first, space_before_last, page, start, end = None, None, None, None, None, None, None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

    if request.method == 'POST':
        formulario = BusquedaPorAnyoPublicacionForm(request.POST)
        if formulario.is_valid():
            start = formulario.cleaned_data.get('start')
            end = formulario.cleaned_data.get('end')
            page = formulario.cleaned_data.get('page')
            if page is None:
                page = 1
            ix = open_dir(populate.whoosh_dir)
            libros = []
            with ix.searcher() as searcher:
                q = NumericRange('anyo_publicacion', start, end)
                books = searcher.search_page(q, page)
                pagecount = books.pagecount
                page = pagecount if page > pagecount else page
                range_loop, space_after_first, space_before_last = calculate_pagination(page, books.pagecount)
                for book in books:
                    libros.append({'id': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'anyo_publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporanyopublicacion.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados,
                   'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': pagecount,
                   'page': page, 'start': start, 'end': end})


def buscar_por_autor(request):
    formulario = BusquedaPorAutorForm()
    libros = None
    recomendados = None
    pagecount, range_loop, space_after_first, space_before_last, page, autor = None, None, None, None, None, None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

    if request.method == 'POST':
        formulario = BusquedaPorAutorForm(request.POST)
        if formulario.is_valid():
            autor = str(formulario.cleaned_data.get('author'))
            page = formulario.cleaned_data.get('page')
            if page is None:
                page = 1
            author_sp = autor.split()

            search_query = ''
            for s in author_sp:
                search_query = search_query + s + "~2 "

            search_query = u'"' + search_query.strip() + '"~2'
            ix = open_dir(populate.whoosh_dir)

            libros = []
            with ix.searcher() as searcher:
                qp = QueryParser('autor', ix.schema)
                books = fuzzy_term_search(qp, searcher, search_query, page)
                pagecount = books.pagecount
                page = pagecount if page > pagecount else page
                range_loop, space_after_first, space_before_last = calculate_pagination(page, books.pagecount)

                for book in books:
                    libros.append({'id': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'anyo_publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaporautor.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados,
                   'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': pagecount,
                   'page': page, 'query_key': 'author', 'query_value': autor})


def buscar_por_titulo(request):
    formulario = BusquedaPorTituloForm()
    libros = None
    recomendados = None
    pagecount, range_loop, space_after_first, space_before_last, page, titulo = None, None, None, None, None, None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

    if request.method == 'POST':
        formulario = BusquedaPorTituloForm(request.POST)
        if formulario.is_valid():
            titulo = str(formulario.cleaned_data.get('title'))
            page = formulario.cleaned_data.get('page')
            if page is None:
                page = 1
            titulo_sp = titulo.split()

            search_query = ''
            for s in titulo_sp:
                search_query = search_query + s + "~2 "

            search_query = u'"' + search_query.strip() + '"~2'
            ix = open_dir(populate.whoosh_dir)

            libros = []
            with ix.searcher() as searcher:
                qp = MultifieldParser(['titulo', 'titulo_original'], schema=ix.schema)
                books = fuzzy_term_search(qp, searcher, search_query, page)
                pagecount = books.pagecount
                page = pagecount if page > pagecount else page
                range_loop, space_after_first, space_before_last = calculate_pagination(page, books.pagecount)

                for book in books:
                    libros.append({'id': book['id'],
                                   'titulo': book['titulo'],
                                   'titulo_original': book['titulo_original'],
                                   'anyo_publicacion': book['anyo_publicacion'],
                                   'autor': book['autor']})

    return render(request, 'busquedaportitulo.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados,
                   'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': pagecount,
                   'page': page, 'query_key': 'title', 'query_value': titulo})


def busqueda_avanzada(request):
    formulario = BusquedaAvanzadaForm()
    libros = None
    recomendados = None
    if request.user.is_authenticated:
        recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user)

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
                        books = fuzzy_term_search(qp, searcher, author_search_query, None)

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
                        books = searcher.search(q, filter=docnums)
                        docnums = set()
                        for result in books:
                            docnums.add(result.docnum)

                    if genre and len(docnums) > 0:
                        qp = QueryParser("genero", schema=ix.schema)
                        q = qp.parse(genre.nombre)
                        books = searcher.search(q, filter=docnums)

                    for book in books:
                        libros.append({'id': book['id'],
                                       'titulo': book['titulo'],
                                       'titulo_original': book['titulo_original'],
                                       'anyo_publicacion': book['anyo_publicacion'],
                                       'autor': book['autor']})

    return render(request, 'busquedaavanzada.html',
                  {'formulario': formulario, 'libros': libros, 'recomendados': recomendados})


def vista_libro(request, id_libro):
    libro = Libro.objects.get(pk=id_libro)
    autores = ", ".join([a.nombre for a in libro.autor.all()])
    relacionados = get_related_items_for_book(ItemFilteringDictionary.dictionary, libro)
    msg = None
    url_casa_libro = 'https://www.casadellibro.com/?q=' + urllib.parse.quote_plus(
        libro.titulo + ' ' + libro.autor.all()[0].nombre)

    if request.method == 'POST' and request.user.is_authenticated:
        if not libro in request.user.saved_books.all():
            request.user.saved_books.add(libro)
            msg = 'Libro guardado correctamente.'
            saved = True
        else:
            request.user.saved_books.remove(libro)
            msg = 'Libro eliminado correctamente de tu lista.'
            saved = False
    elif request.method == 'POST' and not request.user.is_authenticated:
        msg = 'Inicie sesión o regístrese para guardar libros.'
        saved = False
    elif request.user.is_authenticated:
        saved = libro in request.user.saved_books.all()
    else:
        saved = False

    return render(request, 'libro.html', {'libro': libro, 'autores': autores, 'saved': saved, 'msg': msg,
                                          'relacionados': relacionados, 'casa_libro': url_casa_libro})


@login_required
def libros_guardados(request):
    libros_usuario = request.user.saved_books.all()
    p = Paginator(libros_usuario, 10)
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    range_loop, space_after_first, space_before_last = calculate_pagination(page_number, p.num_pages)
    page = p.get_page(page_number)
    for l in page.object_list:
        l.autores = ", ".join([a.nombre for a in l.autor.all()])
    return render(request, 'librosguardados.html',
                  {'libros': page.object_list, 'rangeloop': range_loop, 'space_after_first': space_after_first,
                   'space_before_last': space_before_last, 'pagecount': p.num_pages,
                   'page': page_number, 'get': True})


@login_required
def recomendaciones_usuario(request):
    recomendados = get_recommended_items_for_user(ItemFilteringDictionary.dictionary, request.user, n=20)
    libros = [(libro, ", ".join([a.nombre for a in libro.autor.all()])) for libro in recomendados]
    return render(request, 'recomendaciones.html', {'libros': libros})


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

        f = urllib.request.urlopen(book_url)
        s = BeautifulSoup(f, "lxml")
        authors_string = s.find('div', class_='profile__header').strong.text.strip()
        authors = authors_string.split(',')
        book_info = s.find('div', class_='profile__data').find('ul').find_all('li')
        image_url = s.find('div', class_='profile__data').find('div', class_='photo').div.img['src']
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
        synopsis_div = s.find('div', class_='profile__text')
        if synopsis_div is not None:
            h2 = str(synopsis_div.div.h2)
            p_colaborators = str(synopsis_div.div.find('p', class_='participate'))
            synopsis = synopsis_div.div.decode_contents()
            synopsis = synopsis.replace(h2, '')
            synopsis = synopsis.replace(p_colaborators, '')
        else:
            synopsis = None

        data = (title, original_title, year, authors, genre, publisher, synopsis, image_url)
        l.append(data)
    return l


def get_books():
    l = []

    for i in range(1, 21):
        logger.info('Obteniendo libros de la página ' + str(i) + ' de Lecturalia')
        books = get_books_from('http://www.lecturalia.com/libros/ac/ultimos-actualizados/' + str(i))
        l.extend(books)

    return l


@user_passes_test(lambda u: u.is_superuser, login_url="/")
def populate_app(request):
    books = get_books()
    populate.populate_system(books)
    return redirect('/')


@user_passes_test(lambda u: u.is_superuser, login_url="/")
def populate_recommendation_dict(request):
    dictionary = calculate_similar_items()
    ItemFilteringDictionary.dictionary = dictionary
    serialize_rs_json()

    return redirect('/')
