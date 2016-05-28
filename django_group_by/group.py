__author__ = 'kako'

from django.utils.functional import cached_property


class AggregatedGroup(object):
    """
    Generic object that constructs related objects like a Django model
    from queryset values() data.
    """
    def __init__(self, model, values):
        self._model = model
        self._values = values
        self._populate_attrs()

    @cached_property
    def _data(self):
        """
        Cached data built from instance raw _values as a dictionary.
        """
        data = {}

        # Iterate all keys and values
        for k, v in self._values.items():
            # Split related model fields
            attrs = k.split('__')

            # Set value depending on number of attrs
            if len(attrs) > 1:
                # Related model field, set as nested dict
                m, f = attrs[-2:]
                if m not in data:
                    data[m] = {}
                data[m][f] = v

            else:
                # Own field, set directly
                data[k] = v

        # Return (+cache) data
        return data

    def _populate_attrs(self):
        """
        Populate instance attributes using _data.
        """
        # Iterate all keys and values in data
        for k, v in self._data.items():
            # Process value and set
            if isinstance(v, dict):
                try:
                    # A dict is usually a model, get field, model and initialize
                    f = getattr(self._model, k).field
                    model = f.related_model
                    v = model(**v)

                except AttributeError:
                    # Not a model, skip
                    continue

            # Set that value
            setattr(self, k, v)
