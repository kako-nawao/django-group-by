
from django_values_group import ValuesGroupMixin
from django.db.models.query import QuerySet


class BookQuerySet(QuerySet, ValuesGroupMixin):
    pass
