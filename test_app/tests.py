
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django_group_by.group import AggregatedGroup
from django_group_by.query import GroupByMixin

from .models import Book, Author
from .factories import AuthorFactory, BookFactory


class AggregatedGroupTest(TestCase):

    def test_init(self):
        self.skipTest('')

    @patch.object(AggregatedGroup, '_populate_attrs', MagicMock())
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
            'city': {'name': 'Akropolis'},
            'foundation': {'year': 1}
        })

    def test_populate_attrs(self):
        self.skipTest('')


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
        self.skipTest('')
        # Create two books by same author
        author = AuthorFactory.create()
        BookFactory.create(author=author, title='The Colour of Magic')
        BookFactory.create(author=author, title='The Light Fantastic')

        # Create another book with same title, but different author
        BookFactory.create(title='The Colour of Magic')

        # Group by author, should return two with only author set
        res = Book.objects.group_by('author').distinct()
        self.assertEqual(res.count(), 2)
        for group in res:
            self.assertTrue(type(group.author), Author)
            self.assertEqual(group.title, None)
            self.assertEqual(group.publication_date, None)
            self.assertEqual(group.genre, None)

        # Group by title, still two with only title set
        res = Book.objects.group_by('title')
        self.assertEqual(res.count(), 2)
        for group in res:
            self.assertEqual(group.author, None)
            self.assertTrue(group.title.startswith('The'))
            self.assertEqual(group.publication_date, None)
            self.assertEqual(group.genre, None)
