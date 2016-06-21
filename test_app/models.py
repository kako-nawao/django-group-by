from django.db import models
from .query import BookQuerySet


class Book(models.Model):

    objects = BookQuerySet.as_manager()

    title = models.CharField(max_length=50)
    publication_date = models.DateTimeField()
    author = models.ForeignKey('Author')
    genre = models.ForeignKey('Genre')


class Author(models.Model):
    name = models.CharField(max_length=50)
    nationality = models.ForeignKey('Nation', null=True)


class Genre(models.Model):
    name = models.CharField(max_length=50)


class Nation(models.Model):
    name = models.CharField(max_length=50)
    demonym = models.CharField(max_length=50)
