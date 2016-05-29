__author__ = 'kako'

from django.utils.functional import cached_property


class AggregatedGroup(object):
    """
    Generic object that constructs related objects like a Django model
    from queryset values() data.
    """
    def __init__(self, model, row_values):
        self._model = model
        self._row_values = row_values
        self._set_values()

    @cached_property
    def _data(self):
        """
        Cached data built from instance raw _values as a dictionary.
        """
        d = {}

        # Iterate all keys and values
        for k, v in self._row_values.items():
            # Split related model fields
            attrs = k.rsplit('__', 1)

            # Set value depending case
            if len(attrs) == 2:
                # Related model field, store nested
                fk, fn = attrs
                if fk not in d:
                    d[fk] = {}
                d[fk][fn] = v

            else:
                # Own model field, store directly
                d[k] = v

        # Return (+cache) data
        return d

    def _set_values(self):
        """
        Populate instance with given.
        """
        # Iterate all keys and values in data
        for k, v in self._data.items():
            # If it's a dict, process it (it's probably instance data)
            if isinstance(v, dict):
                try:
                    # Get related model from field (follow path)
                    rel_model = self._model
                    for attr in k.split('__'):
                        rel_model = getattr(rel_model, attr).field.related_model

                except AttributeError:
                    # Not a model, maybe it is a dict field (?)
                    pass

                else:
                    # It is a model, build instance from data
                    k = k.replace('__', '_')
                    v = rel_model(**v)

            # Set value
            setattr(self, k, v)