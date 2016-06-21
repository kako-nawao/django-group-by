
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from django.test import TestCase
from django_group_by import GroupByMixin
from django_group_by.group import AggregatedGroup

from .models import Book, Author, Genre, Nation
from .factories import AuthorFactory, BookFactory, GenreFactory


class AggregatedGroupTest(TestCase):

    @patch.object(AggregatedGroup, '_set_values', MagicMock())
    def test_data(self):
        # Simplest case, no nesting
        agg = AggregatedGroup(None, {'name': 'Peter', 'age': 56})
        self.assertEqual(agg._data, {'name': 'Peter', 'age': 56})

        # First level nesting
        agg = AggregatedGroup(None, {'name': 'Peter', 'friend__age': 56})
        self.assertEqual(agg._data, {'name': 'Peter', 'friend': {'age': 56}})

        # Deep nesting
        agg = AggregatedGroup(None, {'name': 'Peter',
                                     'birth__city__name': 'Akropolis',
                                     'birth__city__foundation__year': 1})
        self.assertEqual(agg._data, {
            'name': 'Peter',
            'birth__city': {'name': 'Akropolis'},
            'birth__city__foundation': {'year': 1}
        })

    def test_init(self):
        # Provide only title, has only that attr
        values = {'title': 'The Colour of Magic'}
        agg = AggregatedGroup(Book, values)
        self.assertEqual(agg.title, 'The Colour of Magic')
        with self.assertRaises(AttributeError):
            agg.publication_date
        with self.assertRaises(AttributeError):
            agg.author
        with self.assertRaises(AttributeError):
            agg.genres

        # FK None (all fields None, including ID), should not init model
        values.update({'author__id': None, 'author__name': None})
        agg = AggregatedGroup(Book, values)
        self.assertEqual(agg.author, None)

        # Change to FK values, without ID
        values.pop('author__id')
        values.update({'author__name': 'Terry Pratchett', 'genres__name': 'Fantasy'})
        agg = AggregatedGroup(Book, values)
        self.assertEqual(type(agg.author), Author)
        self.assertEqual(agg.author.name, 'Terry Pratchett')
        self.assertEqual(type(agg.genres), Genre)
        self.assertEqual(agg.genres.name, 'Fantasy')

        # Deep relations, make sure it's followed properly
        values.update({'author__nationality__name': 'Great Britain',
                       'author__nationality__demonym': 'British'})
        agg = AggregatedGroup(Book, values)
        self.assertEqual(type(agg.author_nationality), Nation)
        self.assertEqual(agg.author_nationality.name, 'Great Britain')
        self.assertEqual(agg.author_nationality.demonym, 'British')


class QuerySetTest(TestCase):

    def test_expand_group_by_field(self):
        # Own fields, not modified
        fields = GroupByMixin._expand_group_by_fields(Book, ['title', 'publication_date'])
        self.assertEqual(set(fields), {'title', 'publication_date'})

        # Related model field, same
        fields = GroupByMixin._expand_group_by_fields(Book, ['author__id', 'genres__name'])
        self.assertEqual(set(fields), {'author__id', 'genres__name'})

        # Related model, must expand
        fields = GroupByMixin._expand_group_by_fields(Book, ['author', 'genres'])
        self.assertEqual(set(fields), {'author__id', 'author__name', 'author__nationality_id',
                                       'genres__id', 'genres__name'})

        # Related model two levels deep, must expand all
        fields = GroupByMixin._expand_group_by_fields(Book, ['author', 'author__nationality', 'genres'])
        self.assertEqual(set(fields), {'author__id', 'author__name', 'author__nationality_id',
                                       'author__nationality__id', 'author__nationality__name',
                                       'author__nationality__demonym', 'genres__id', 'genres__name'})

    def test_group_by(self):
        # Create two books by same author
        author1 = AuthorFactory.create(name='Terry Pratchett', nationality__name='Great Britain')
        book1 = BookFactory.create(author=author1, title='The Colour of Magic')
        book2 = BookFactory.create(author=author1, title='The Light Fantastic')

        # Create another book with same title, but different author
        author2 = AuthorFactory.create(nationality=None)
        BookFactory.create(author=author2, title='The Colour of Magic')

        # Add genres to books 1-2
        fantasy = GenreFactory.create(name='Fantasy')
        comedy = GenreFactory.create(name='Comedy')
        book1.genres.add(fantasy, comedy)
        book2.genres.add(fantasy, comedy)

        # Group by author, should return two with only author set
        res = Book.objects.group_by('author').order_by('author').distinct()
        self.assertEqual(res.count(), 2)
        for group in res:
            self.assertTrue(type(group.author), Author)
            with self.assertRaises(AttributeError):
                group.title
            with self.assertRaises(AttributeError):
                group.publication_date
            with self.assertRaises(AttributeError):
                group.genre

        # Check that they're authors 1 and 2
        tp, oth = res.all()
        self.assertEqual(tp.author, author1)
        self.assertEqual(oth.author, author2)

        # Group by title, still two with only title set
        res = Book.objects.group_by('title').distinct()
        self.assertEqual(res.count(), 2)
        for group in res:
            with self.assertRaises(AttributeError):
                group.author
            self.assertTrue(group.title.startswith('The'))
            with self.assertRaises(AttributeError):
                group.publication_date
            with self.assertRaises(AttributeError):
                group.genre

        # Group by nationality, only attr author_nationality is included
        # Note: invert order because None goes first
        res = Book.objects.group_by('author__nationality').order_by('-author__nationality').distinct()
        self.assertEqual(res.count(), 2)
        tp, oth = res.all()
        self.assertEqual(tp.author_nationality, author1.nationality)
        self.assertEqual(tp.author_nationality.name, 'Great Britain')
        with self.assertRaises(AttributeError):
            tp.title
        with self.assertRaises(AttributeError):
            tp.author
        self.assertEqual(oth.author_nationality, None)
        with self.assertRaises(AttributeError):
            oth.title
        with self.assertRaises(AttributeError):
            oth.author

        # Group by title+genre, should expand to 5 groups
        res = Book.objects.group_by('title', 'genres').order_by('genres__name', 'title').distinct()
        self.assertEqual(res.count(), 5)
        b1, b2, b3, b4, b5 = res.all()
        self.assertEqual(b1.genres, None)
        self.assertEqual(b1.title, 'The Colour of Magic')
        self.assertEqual(b2.genres, comedy)
        self.assertEqual(b2.title, 'The Colour of Magic')
        self.assertEqual(b3.genres, comedy)
        self.assertEqual(b3.title, 'The Light Fantastic')
        self.assertEqual(b4.genres, fantasy)
        self.assertEqual(b4.title, 'The Colour of Magic')
        self.assertEqual(b5.genres, fantasy)
        self.assertEqual(b5.title, 'The Light Fantastic')
