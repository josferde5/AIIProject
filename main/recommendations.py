from decimal import Decimal
from .models import Libro
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import string

stopwords = stopwords.words('spanish')


def cosine_sim_vectors(v1, v2):
    v1 = v1.reshape(1, -1)
    v2 = v2.reshape(1, -1)

    return cosine_similarity(v1, v2)[0][0]


def clean_string(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stopwords])

    return text


def tf_idf_similarity(text1, text2):
    sentences = [text1, text2]
    sim = 0
    if text1 is not None and text2 is not None:
        cleaned_sentences = list(map(clean_string, sentences))
        try:
            tfidf = TfidfVectorizer(analyzer='word', ngram_range=(2, 2), min_df=1)
            vect = tfidf.fit_transform(cleaned_sentences)
            sim = cosine_sim_vectors(vect[0], vect[1])
        except ValueError:
            sim = 0

    return sim


def similarity(book1, book2):
    title_sim = Decimal(tf_idf_similarity(book1.titulo, book2.titulo))
    synopsis_sim = Decimal(tf_idf_similarity(book1.sinopsis, book2.sinopsis))

    genre_sim = 1 if book1.genero == book2.genero else 0
    author_sim = 1 if book1.autor == book2.autor else 0

    return Decimal(0.3) * title_sim + Decimal(0.3) * synopsis_sim + Decimal(0.2) * genre_sim + Decimal(0.2) * author_sim


def top_matches(books, book, n=3):
    scores = [(similarity(book, other), other) for other in books if other != book]

    scores.sort()
    scores.reverse()
    return scores[0:n]


def calculate_similar_items(n=10):
    result = {}
    books = Libro.objects.all()
    c = 0

    for item in books:
        c += 1
        if c % 10 == 0:
            print("%d / %d" % (c, len(books)))
        scores = top_matches(books, item, n=n)
        result[item] = scores

    return result


def get_recommended_items_for_user(item_match, user, n=4):
    saved_books = user.saved_books.all()
    rankings = []

    if len(saved_books) == 0:
        books = Libro.objects.filter(genero=user.genre)[:n]
    else:
        for book in saved_books:
            recommended = [(sim, book2) for (sim, book2) in item_match[book] if book2 not in saved_books]
            rankings.extend(recommended)
        rankings.sort()
        rankings.reverse()

        if not isinstance(rankings, Libro):
            books = [book for (sim, book) in rankings]
            books = list(dict.fromkeys(books))[:n]
        else:
            books = [rankings]

    return books


def get_related_items_for_book(item_match, book):
    rankings = item_match[book]
    rankings.sort()
    rankings.reverse()
    return [book for (sim, book) in rankings][:4]


class ItemFilteringDictionary:
    dictionary = {}
