from django.test import TestCase

from .models import Book, Author, Nation, Genre
from .factories import AuthorFactory, BookFactory


class BookQuerySetTest(TestCase):

    def test_group_by(self):
        # Create two books by same author
        author = AuthorFactory.create()
        BookFactory.create(author=author, title='The Colour of Magic')
        BookFactory.create(author=author, title='The Light Fantastic')

        # Create another book with same title, but different author
        BookFactory.create(title='The Colour of Magic')

        # Group by author, should return two with only author set
        res = Book.objects.group_by('author')
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
