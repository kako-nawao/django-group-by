"""
This module contains the implementations for Django 1.9 and above, for which we
need a customized ValuesIterable.
"""
from django.db.models.query import ValuesIterable

from .group import AggregatedGroup


class GroupByIterable(ValuesIterable):
    """
    Modified ValuesIterable that yields AggregatedGroup instances instead
    of dictionaries, which resemble the queryset's model in that all foreign
    related field values become actual model instances.
    """
    def __iter__(self):
        # Same as in django
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)
        field_names = list(query.values_select)
        extra_names = list(query.extra_select)
        annotation_names = list(query.annotation_select)
        names = extra_names + field_names + annotation_names

        # Iterate results and yield AggregatedGroup instances
        for row in compiler.results_iter():
            data = dict(zip(names, row))
            obj = AggregatedGroup(queryset.model, data)
            yield obj


class GroupByIterableMixinBase(object):
    """
    Implementation of the group_by method using GroupByIterable.
    """
    def group_by(self, *fields):
        """
        Clone the queryset using GroupByQuerySet.

        :param fields:
        :return:
        """
        fields = self._expand_group_by_fields(self.model, fields)
        clone = self._values(*fields)
        clone._iterable_class = GroupByIterable
        return clone
