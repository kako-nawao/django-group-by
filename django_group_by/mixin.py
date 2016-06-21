"""
This module contains the final mixin implementation, for whatever version
of Django is present.
"""
from django.db.models import ForeignKey, ManyToManyField

try:
    # Django 1.9+
    from .iterable import GroupByIterableMixinBase as GroupByMixinBase

except ImportError:
    # Django 1.8-
    from .queryset import GroupByQuerySetMixinBase as GroupByMixinBase


class GroupByMixin(GroupByMixinBase):
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

                if isinstance(model_field, (ForeignKey, ManyToManyField)):
                    # It's a related field, get model
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
