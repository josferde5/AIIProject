from .models import Autor, Genero, Editorial, Libro
from whoosh.fields import Schema, TEXT, NUMERIC, ID
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

    schem = Schema(id=ID(stored=True), titulo=TEXT(stored=True), titulo_original=TEXT(stored=True),
                   anyo_publicacion=NUMERIC(int, 32, signed=False, stored=True), autor=TEXT(stored=True),
                   genero=TEXT(stored=True), editorial=TEXT(stored=True), sinopsis=TEXT)

    if os.path.exists(whoosh_dir):
        shutil.rmtree(whoosh_dir)
    os.mkdir(whoosh_dir)

    ix = create_in(whoosh_dir, schema=schem)
    writer = ix.writer()

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
        l = Libro.objects.create(titulo=book[0], titulo_original=book[1], anyo_publicacion=int(book[2]),
                                 autor=author, genero=genre, editorial=publisher, sinopsis=book[6],
                                 url_imagen=book[7])

        writer.add_document(id=str(l.id), titulo=book[0], titulo_original=book[1], anyo_publicacion=int(book[2]),
                            autor=book[3], genero=book[4], editorial=book[5], sinopsis=book[6])

    writer.commit()
    logger.info('Whoosh index has been created successfully.')
    logger.info('Django has been populated successfully. ' + str(len(books)) + ' books added.')
