from .models import Autor, Genero, Editorial, Libro, TodosTusLibros
from whoosh.fields import Schema, TEXT, NUMERIC, KEYWORD, ID
from whoosh.index import create_in
import logging
import os
import shutil

whoosh_dir = 'Index'
logger = logging.getLogger(__name__)


def populate_system(books):
    Autor.objects.all().delete()
    Genero.objects.all().delete()
    Editorial.objects.all().delete()
    Libro.objects.all().delete()

    schem = Schema(id=ID(unique=True, stored=True), titulo=TEXT(stored=True), titulo_original=TEXT(stored=True),
                   anyo_publicacion=NUMERIC(int, 32, signed=True, stored=True), autor=TEXT(stored=True),
                   genero=TEXT(stored=True), editorial=TEXT(stored=True), sinopsis=TEXT)

    if os.path.exists(whoosh_dir):
        shutil.rmtree(whoosh_dir)
    os.mkdir(whoosh_dir)

    ix = create_in(whoosh_dir, schema=schem)
    writer = ix.writer()

    for book in books:
        if book[2].strip().endswith('a. C.'):
            year_string = '-' + book[2].strip().replace(' a. C.', '')
            year = int(year_string)
        else:
            year = int(book[2])
        authors = book[3]
        genre_name = book[4]
        genre, created = Genero.objects.get_or_create(nombre=genre_name)
        publisher_name = book[5]
        precio = book[8]
        libro_url = book[9]

        if publisher_name is not None:
            publisher, created = Editorial.objects.get_or_create(nombre=publisher_name)
        else:
            publisher = None

        if precio is not None and libro_url is not None:
            todos_tus_libros = TodosTusLibros.objects.create(precio=precio, url=libro_url)
            todos_tus_libros.save()
        else:
            todos_tus_libros = None

        l, created = Libro.objects.get_or_create(titulo=book[0], titulo_original=book[1], anyo_publicacion=year,
                                                 genero=genre, editorial=publisher, sinopsis=book[6],
                                                 url_imagen=book[7], todos_tus_libros=todos_tus_libros)
        if created:
            for a in authors:
                author, created = Autor.objects.get_or_create(nombre=a)
                l.autor.add(author)
            authors_string = ", ".join(authors)
            writer.add_document(id=str(l.id), titulo=book[0], titulo_original=book[1], anyo_publicacion=year,
                                autor=authors_string, genero=book[4], editorial=book[5], sinopsis=book[6])

    writer.commit()
    logger.info('El índice de Whoosh se ha creado correctamente.')
    logger.info('Django ha sido populado satisfactoriamente. ' + str(len(books)) + ' libros añadidos.')
