"""This module contains the tracked object classes.

TrackedObject forms the basis for both the TrackedDict and the TrackedList.

A function for automatic conversion of dicts and lists to their tracked
counterparts is also included.
"""

import itertools
import logging

from six import iteritems
from sqlalchemy.ext.mutable import Mutable


logger = logging.getLogger(__name__)


class TrackedObject(object):
    """A base class for delegated change-tracking."""
    _type_mapping = {}

    def __init__(self, *args, **kwds):
        self.parent = None
        super(TrackedObject, self).__init__(*args, **kwds)

    def changed(self, message=None, *args):
        """Marks the object as changed.

        If a `parent` attribute is set, the `changed()` method on the parent
        will be called, propagating the change notification up the chain.

        The message (if provided) will be debug logged.
        """
        if message is not None:
            logger.debug('%s: %s', self._repr(), message % args)
        logger.debug('%s: changed', self._repr())
        if self.parent is not None:
            self.parent.changed()
        elif isinstance(self, Mutable):
            super(TrackedObject, self).changed()

    @classmethod
    def register(cls, origin_type):
        """Decorator for mutation tracker registration.

        The provided `origin_type` is mapped to the decorated class such that
        future calls to `convert()` will convert the object of `origin_type`
        to an instance of the decorated class.
        """
        def decorator(tracked_type):
            """Adds the decorated class to the `_type_mapping` dictionary."""
            cls._type_mapping[origin_type] = tracked_type
            return tracked_type
        return decorator

    @classmethod
    def convert(cls, obj, parent):
        """Converts objects to registered tracked types

        This checks the type of the given object against the registered tracked
        types. When a match is found, the given object will be converted to the
        tracked type, its parent set to the provided parent, and returned.

        If its type does not occur in the registered types mapping, the object
        is returned unchanged.
        """
        replacement_type = cls._type_mapping.get(type(obj))
        if replacement_type is not None:
            new = replacement_type(obj)
            new.parent = parent
            return new
        return obj

    def convert_iterable(self, iterable):
        """Generator to `convert` every member of the given iterable."""
        return (self.convert(item, self) for item in iterable)

    def convert_items(self, items):
        """Generator like `convert_iterable`, but for 2-tuple iterators."""
        return ((key, self.convert(value, self)) for key, value in items)

    def convert_mapping(self, mapping):
        """Convenience method to track either a dict or a 2-tuple iterator."""
        if isinstance(mapping, dict):
            return self.convert_items(iteritems(mapping))
        return self.convert_items(mapping)

    def _repr(self):
        """Simple object representation."""
        return '<%(namespace)s.%(type)s object at 0x%(address)0xd>' % {
            'namespace': __name__,
            'type': type(self).__name__,
            'address': id(self)}


@TrackedObject.register(dict)
class TrackedDict(TrackedObject, dict):
    """A TrackedObject implementation of the basic dictionary."""
    def __init__(self, source=(), **kwds):
        super(TrackedDict, self).__init__(itertools.chain(
            self.convert_mapping(source),
            self.convert_mapping(kwds)))

    def __setitem__(self, key, value):
        self.changed('__setitem__: %r=%r', key, value)
        super(TrackedDict, self).__setitem__(key, self.convert(value, self))

    def __delitem__(self, key):
        self.changed('__delitem__: %r', key)
        super(TrackedDict, self).__delitem__(key)

    def clear(self):
        self.changed('clear')
        super(TrackedDict, self).clear()

    def pop(self, *key_and_default):
        self.changed('pop: %r', key_and_default)
        return super(TrackedDict, self).pop(*key_and_default)

    def popitem(self):
        self.changed('popitem')
        return super(TrackedDict, self).popitem()

    def update(self, source=(), **kwds):
        self.changed('update(%r, %r)', source, kwds)
        super(TrackedDict, self).update(itertools.chain(
            self.convert_mapping(source),
            self.convert_mapping(kwds)))

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]

        # this calls __setitem__, which converts the value and calls changed()
        self[key] = default
        # the value at self[key] may be a new TrackedObject, so return
        # self[key] instead of default
        return self[key]


@TrackedObject.register(list)
class TrackedList(TrackedObject, list):
    """A TrackedObject implementation of the basic list."""
    def __init__(self, iterable=()):
        super(TrackedList, self).__init__(self.convert_iterable(iterable))

    def __setitem__(self, key, value):
        self.changed('__setitem__: %r=%r', key, value)
        super(TrackedList, self).__setitem__(key, self.convert(value, self))

    def __delitem__(self, key):
        self.changed('__delitem__: %r', key)
        super(TrackedList, self).__delitem__(key)

    def append(self, item):
        self.changed('append: %r', item)
        super(TrackedList, self).append(self.convert(item, self))

    def extend(self, iterable):
        self.changed('extend: %r', iterable)
        super(TrackedList, self).extend(self.convert_iterable(iterable))

    def remove(self, value):
        self.changed('remove: %r', value)
        return super(TrackedList, self).remove(value)

    def pop(self, index):
        self.changed('pop: %d', index)
        return super(TrackedList, self).pop(index)

    def sort(self, cmp=None, key=None, reverse=False):
        self.changed('sort')
        super(TrackedList, self).sort(cmp=cmp, key=key, reverse=reverse)
