"""
This module contains the implementations for Django 1.8 and below, for which we
need a customized ValuesQuerySet.
"""
from django.db.models.query import ValuesQuerySet

from .group import AggregatedGroup


class GroupByQuerySet(ValuesQuerySet):
    """
    Modified ValuesQuerySet that yields AggregatedGroup instances instead
    of dictionaries, which resemble the queryset's model in that all foreign
    related field values become actual model instances.
    """
    def iterator(self):
        # Same as in django
        extra_names = list(self.query.extra_select)
        field_names = self.field_names
        annotation_names = list(self.query.annotation_select)
        names = extra_names + field_names + annotation_names

        # Iterate results and yield AggregatedGroup instances
        for row in self.query.get_compiler(self.db).results_iter():
            data = dict(zip(names, row))
            obj = AggregatedGroup(self.model, data)
            yield obj


class GroupByQuerySetMixinBase(object):
    """
    Implementation of the group_by method using GroupByQuerySet.
    """
    def group_by(self, *fields):
        """
        Clone the queryset using GroupByQuerySet.

        :param fields:
        :return:
        """
        fields = self._expand_group_by_fields(self.model, fields)
        return self._clone(klass=GroupByQuerySet, setup=True, _fields=fields)
