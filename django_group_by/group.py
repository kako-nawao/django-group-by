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

    def __repr__(self):
        return u'<{} for {}>'.format(self.__class__.__name__,
                                     self._model.__name__)

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
                    # Model, first shorten field name
                    k = k.replace('__', '_')

                    # Now init instance if required (not if we got ID None)
                    if 'id' in v and v['id'] is None:
                        # This means we grouped by ID, if it's none then FK is None
                        v = None

                    else:
                        # Either we have ID or we didn't group by ID, use instance
                        v = rel_model(**v)

            # Set value
            setattr(self, k, v)
