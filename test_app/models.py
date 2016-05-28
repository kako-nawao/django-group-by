from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=50)
    publication_date = models.DateTimeField()
    author = models.ForeignKey('Author')
    genre = models.ForeignKey('Genre')


class Author(models.Model):
    name = models.CharField(max_length=50)
    nationality = models.ForeignKey('Nation')


class Genre(models.Model):
    name = models.CharField(max_length=50)


class Nation(models.Model):
    name = models.CharField(max_length=50)
    demonyn = models.CharField(max_length=50)
