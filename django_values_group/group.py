__author__ = 'kako'


class ValuesGroup(object):
    """
    Generic object that constructs related objects like a Django model
    from queryset values() data. This is used as a workaround for Django's
    shitty behaviour of returning dicts instead of instances when using
    values() to group.
    """
    def __init__(self, model, values):
        self._model = model
        self._values = values
        self._build_data()
        self._populate_attrs()

    def _build_data(self):
        self._data = {}
        for k, v in self._values.items():
            attrs = k.split('__')
            first_attr = attrs[0]
            if len(attrs) > 1:
                if first_attr not in self._data:
                    self._data[first_attr] = {}
                for attr in attrs[1:]:
                    self._data[first_attr][attr] = v

            else:
                self._data[k] = v

    def _populate_attrs(self):
        for k, v in self._data.items():
            if isinstance(v, dict):
                try:
                    model = getattr(self._model, k).field.related.to
                    v = model(**v)
                except AttributeError:
                    continue
            setattr(self, k, v)
