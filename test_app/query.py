
from django_group_by import GroupByMixin
from django.db.models.query import QuerySet


class BookQuerySet(QuerySet, GroupByMixin):
    pass
