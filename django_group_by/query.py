__author__ = 'kako'

from django.db.models.query import ValuesQuerySet
from django.db.models import ForeignKey

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


class GroupByMixin(object):
    """
    QuerySet mixin that adds a group_by() method, similar to values() but
    which returns AggregatedGroup instances when iterated instead of
    dictionaries.
    """
    @classmethod
    def _expand_group_by_fields(cls, model, fields):
        """
        Expand FK fields into all related object's fields to avoid future
        lookups.

        :param fields: fields to "group by"
        :return: expanded fields
        """
        # Containers for resulting fields and related model fields
        res = []
        related = {}

        # Add own fields and populate related fields
        for field_name in fields:
            if '__' in field_name:
                # Related model field: append to related model's fields
                fk_field_name, related_field = field_name.split('__', 1)
                if fk_field_name not in related:
                    related[fk_field_name] = [related_field]
                else:
                    related[fk_field_name].append(related_field)

            else:
                # Simple field, get the field instance
                model_field = model._meta.get_field(field_name)

                if isinstance(model_field, ForeignKey):
                    # It's a FK, get model
                    related_model = model_field.related_model

                    # Append all its fields with the correct prefix
                    res.extend('{}__{}'.format(field_name, f.column)
                               for f in related_model._meta.fields)

                else:
                    # It's a common field, just append it
                    res.append(field_name)

        # Resolve all related fields
        for fk_field_name, field_names in related.items():
            # Get field
            fk = model._meta.get_field(fk_field_name)

            # Get all fields for that related model
            related_fields = cls._expand_group_by_fields(fk.related_model,
                                                         field_names)

            # Append them with the correct prefix
            res.extend('{}__{}'.format(fk_field_name, f) for f in related_fields)

        # Return all fields
        return res

    def group_by(self, *fields):
        """
        Clone the queryset using GroupByQuerySet.

        :param fields:
        :return:
        """
        fields = self._expand_group_by_fields(self.model, fields)
        return self._clone(klass=GroupByQuerySet, setup=True, _fields=fields)
