==============
Django GroupBy
==============

.. image:: https://img.shields.io/pypi/l/django-group-by.svg
    :target: http://www.opensource.org/licenses/MIT

.. image:: https://img.shields.io/pypi/pyversions/django-group-by.svg
    :target: https://pypi.python.org/pypi/django-group-by
.. image:: https://img.shields.io/pypi/v/django-group-by.svg
    :target: https://pypi.python.org/pypi/django-group-by

.. image:: https://img.shields.io/travis/kako-nawao/django-group-by.svg
    :target: https://travis-ci.org/kako-nawao/django-group-by
.. image:: https://img.shields.io/coveralls/kako-nawao/django-group-by.svg
    :target: https://coveralls.io/github/kako-nawao/django-group-by

This package provides a mixin for Django QuerySets that adds a method ``group_by`` that
behaves mostly like the ``values`` method, but with one difference: its iterator does not
return dictionaries, but a *model-like object with model instances for related values*.

Installation
============

Install from PyPI::

    pip install django-group-by

Compatibility
~~~~~~~~~~~~~

This package is compatible with Django 1.8 and 1.9, and Python versions 2.7, 3.4 and 3.5.
Probably others, but those 6 combinations are the ones against which we build (by Travis CI).


Usage
=====

Create a QuerySet subclass with the ``GroupByMixin`` to use in a model's manager::

    # models.py

    from django.db import models
    from django.db.models.query import QuerySet
    from django_group_by import GroupByMixin

    class BookQuerySet(QuerySet, GroupByMixin):
        pass

    class Book(Model):
        objects = BookQuerySet.as_manager()

        title = models.CharField(max_length=100)
        author = models.ForeignKey('another_app.Author')
        publication_date = models.DateField()
    ...

Then use it just like ``values``, and you'll get a similar query set::

    >>> some_rows = Book.objects.group_by('title', 'author', 'author__nationality').distinct()
    >>> some_rows.count()
    4

The difference is that every row is not a dictionary but an AggregatedGroup instance, with only the grouped fields::

    >>> row = some_rows[0]
    >>> row
    <AggregatedGroup for Book>
    >>> row.title
    The Colour of Magic
    >>> row.publication_date
    *** AttributeError: 'AggregatedGroup' object has no attribute 'publication_date'

But of course the main advantage is that you also get related model instances, as far as you want::

    >>> row.author
    <Author: Terry Pratchett>
    >>> row.author_nationality
    <Nation: Great Britain>


Related Model ID Only
~~~~~~~~~~~~~~~~~~~~~

The previous example shows a difference in behaviour from Django's ``values``: we're grouping by the foreign key
*author*, but instead of getting only the ID we get the full instance. Why? Because it's more useful, and I
think that getting *{'author': 5}* as a result is just weird.

If you just want the ID you can specify it::

    >>> some_rows = Book.objects.group_by('title', 'author_id', 'author__nationality_id').distinct()

