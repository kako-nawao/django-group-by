__author__ = 'kako'

from django.db.models.query import QuerySet, ValuesQuerySet

from .group import ValuesGroup


class ValuesGroupQuerySet(ValuesQuerySet):
    """
    Modified ValuesQuerySet that yields ValuesGroup instances instead
    of dictionaries, which means that you can still expect a model-like
    behaviour for APIs and whatnot. It just works.
    """
    def iterator(self):
        # Same as in django
        extra_names = list(self.query.extra_select)
        field_names = self.field_names
        annotation_names = list(self.query.annotation_select)
        names = extra_names + field_names + annotation_names

        # Iterate results and yield ValuesGroup instances
        for row in self.query.get_compiler(self.db).results_iter():
            data = dict(zip(names, row))
            obj = ValuesGroup(model=self.model, values=data)
            yield obj


class ValuesGroupMixin(QuerySet):
    """
    QuerySet mixin that uses ValuesGroupQuerySet as the values() queryset
    instead of the standard shitty one..
    """
    def values(self, *fields):
        return self._clone(klass=ValuesGroupQuerySet, setup=True, _fields=fields)

