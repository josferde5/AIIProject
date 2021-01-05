from django.shortcuts import render, redirect
from .admin import UserCreateForm
from django.contrib.auth import logout as log_out, login as log_in, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
import urllib.request
from bs4 import BeautifulSoup
from .models import Autor, Genero, Editorial, Libro
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
    total_pages = int(pagination_links[len(pagination_links)-1].string.strip())

    for i in range(1, 2):
        books = get_books_from('http://www.lecturalia.com/libros/ac/ultimos-actualizados/' + str(i))
        l.extend(books)
    return l


def populate_whoosh(books):
    pass


def populate_django(books):
    Autor.objects.all().delete()
    Genero.objects.all().delete()
    Editorial.objects.all().delete()
    Libro.objects.all().delete()
    for book in books:
        author_name = book[3]
        author, created = Autor.objects.get_or_create(nombre=author_name)
        genre_name = book[4]
        genre, created = Genero.objects.get_or_create(nombre=genre_name)
        publisher_name = book[5]
        if publisher_name is not None:
            publisher, created = Editorial.objects.get_or_create(nombre=publisher_name)
        else:
            publisher = None
        book = Libro.objects.create(titulo=book[0], titulo_original=book[1], anyo_publicacion=int(book[2]),
                                    autor=author, genero=genre, editorial=publisher, sinopsis=book[6])


@user_passes_test(lambda u: u.is_superuser, login_url="/")
def populate(request):
    books = get_books()
    populate_whoosh(books)
    populate_django(books)

    return redirect('/')
    

