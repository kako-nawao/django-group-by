
from factory import SubFactory, DjangoModelFactory, Faker, LazyAttribute

from .models import Author, Book, Genre, Nation


class GenreFactory(DjangoModelFactory):

    class Meta(object):
        model = Genre
        django_get_or_create = ('name',)

    name = Faker('random_element', elements=('Adventure', 'Fantasy', 'Science-Fiction', 'Comedy',))


class NationalityFactory(DjangoModelFactory):

    class Meta(object):
        model = Nation
        django_get_or_create = ('name',)

    name = Faker('country')
    demonym = LazyAttribute(lambda obj: '{}an'.format(obj.name))


class AuthorFactory(DjangoModelFactory):

    class Meta(object):
        model = Author
        django_get_or_create = ('name', 'nationality',)

    name = Faker('name')
    nationality = SubFactory(NationalityFactory)


class BookFactory(DjangoModelFactory):

    class Meta(object):
        model = Book

    title = Faker('sentence')
    publication_date = Faker('date_time')
    author = SubFactory(AuthorFactory)
