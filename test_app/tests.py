
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from django.test import TestCase
from django_group_by.group import AggregatedGroup
from django_group_by.query import GroupByMixin

from .models import Book, Author, Genre, Nation
from .factories import AuthorFactory, BookFactory


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
            agg.genre

        # Provide also related models
        values.update({'author__name': 'Terry Pratchett', 'genre__name': 'Fantasy'})
        agg = AggregatedGroup(Book, values)
        self.assertEqual(type(agg.author), Author)
        self.assertEqual(agg.author.name, 'Terry Pratchett')
        self.assertEqual(type(agg.genre), Genre)
        self.assertEqual(agg.genre.name, 'Fantasy')

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
        fields = GroupByMixin._expand_group_by_fields(Book, ['author__id', 'genre__name'])
        self.assertEqual(set(fields), {'author__id', 'genre__name'})

        # Related model, must expand
        fields = GroupByMixin._expand_group_by_fields(Book, ['author', 'genre'])
        self.assertEqual(set(fields), {'author__id', 'author__name', 'author__nationality_id',
                                       'genre__id', 'genre__name'})

        # Related model two levels deep, must expand all
        fields = GroupByMixin._expand_group_by_fields(Book, ['author', 'author__nationality', 'genre'])
        self.assertEqual(set(fields), {'author__id', 'author__name', 'author__nationality_id',
                                       'author__nationality__id', 'author__nationality__name',
                                       'author__nationality__demonym', 'genre__id', 'genre__name'})

    def test_group_by(self):
        # Create two books by same author
        author1 = AuthorFactory.create(name='Terry Pratchett', nationality__name='Great Britain')
        BookFactory.create(author=author1, title='The Colour of Magic')
        BookFactory.create(author=author1, title='The Light Fantastic')

        # Create another book with same title, but different author
        author2 = AuthorFactory.create(nationality__name='United States')
        BookFactory.create(author=author2, title='The Colour of Magic')

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
        res = Book.objects.group_by('author__nationality').order_by('author__nationality').distinct()
        self.assertEqual(res.count(), 2)
        tp, oth = res.all()
        self.assertEqual(tp.author_nationality, author1.nationality)
        self.assertEqual(tp.author_nationality.name, 'Great Britain')
        with self.assertRaises(AttributeError):
            tp.title
        with self.assertRaises(AttributeError):
            tp.author
        self.assertEqual(oth.author_nationality, author2.nationality)
        self.assertEqual(oth.author_nationality.name, 'United States')
        with self.assertRaises(AttributeError):
            oth.title
        with self.assertRaises(AttributeError):
            oth.author
