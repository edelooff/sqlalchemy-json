#!/usr/bin/python
"""This module contains the tracked object classes.

TrackedObject forms the basis for both the TrackedDict and the TrackedList.

A function for automatic conversion of dicts and lists to their tracked
counterparts is also included.
"""

# Standard modules
import itertools
import logging


class TrackedObject(object):
  """A base class for delegated change-tracking."""
  _type_mapping = {}
  parent = None

  def __init__(self, *args, **kwds):
    self.logger = logging.getLogger(type(self).__name__)
    self.logger.debug('%s: __init__' % self._repr())
    super(TrackedObject, self).__init__(*args, **kwds)

  def changed(self, message=None, *args):
    """Used to mark the object as changed.

    If a `parent` attribute is set, the `changed` method on the parent will also
    be called, bubbling the change up to the top of the chain.

    The message (if provided) will be debug logged.
    """
    if message is not None:
      self.logger.debug('%s: %s' % (self._repr(), message % args))
    self.logger.debug('%s: changed' % self._repr())
    if self.parent is not None:
      self.parent.changed()

  @classmethod
  def register(cls, origin_type):
    """Registers the class decorated with this method as a mutation tracker.

    The provided `origin_type` is mapped to the decorated class such that
    future calls to `convert()` will convert the object of `origin_type` to an
    instance of the decorated class.
    """
    def decorator(tracked_type):
      cls._type_mapping[origin_type] = tracked_type
      return tracked_type
    return decorator

  @classmethod
  def convert(cls, obj, parent):
    """Converts objects to tracked types.

    This allows the new structure to track changes and propagate them to the
    provided parent.
    """
    obj_type = type(obj)
    for type_, converter in cls._type_mapping.iteritems():
      if obj_type is type_:
        new = converter(obj)
        new.parent = parent
        return new
    return obj

  @classmethod
  def convert_iterable(cls, iterable, parent):
    """Returns a generator that performs `_track` on every of its members."""
    return (cls.convert(item, parent) for item in iterable)

  @classmethod
  def convert_iteritems(cls, iteritems, parent):
    """Returns a generator like `_track_iterable` for 2-tuple item-iterators."""
    return ((key, cls.convert(value, parent)) for key, value in iteritems)

  @classmethod
  def convert_mapping(cls, mapping, parent):
    """Convenience method to track either a dict or a 2-tuple iterator."""
    if isinstance(mapping, dict):
      return cls.convert_iteritems(mapping.iteritems(), parent)
    return cls.convert_iteritems(mapping, parent)

  def _repr(self):
    """Object representation that includes the memory address."""
    return '<%(namespace)s.%(type)s object at 0x%(address)0xd>' % {
        'namespace': __name__,
        'type': type(self).__name__,
        'address': id(self)}


@TrackedObject.register(dict)
class TrackedDict(TrackedObject, dict):
  """A TrackedObject implementation of the basic dictionary."""
  def __init__(self, source=(), **kwds):
    super(TrackedDict, self).__init__(itertools.chain(
        self.convert_mapping(source, self),
        self.convert_mapping(kwds, self)))

  def __setitem__(self, key, value):
    self.changed('__setitem__: %r=%r', key, value)
    return super(TrackedDict, self).__setitem__(key, self.convert(value, self))

  def __delitem__(self, key):
    self.changed('__delitem__: %r', key)
    return super(TrackedDict, self).__delitem__(key)

  def update(self, source=(), **kwds):
    self.changed('update(%r, %r)', source, kwds)
    super(TrackedDict, self).update(itertools.chain(
        self.convert_mapping(source, self),
        self.convert_mapping(kwds, self)))


@TrackedObject.register(list)
class TrackedList(TrackedObject, list):
  """A TrackedObject implementation of the basic list."""
  def __init__(self, iterable=()):
    super(TrackedList, self).__init__(self.convert_iterable(iterable, self))

  def __setitem__(self, key, value):
    self.changed('__setitem__: %r=%r', key, value)
    return super(TrackedList, self).__setitem__(key, self.convert(value, self))

  def __delitem__(self, key):
    self.changed('__delitem__: %r', key)
    return super(TrackedList, self).__delitem__(key)

  def append(self, item):
    self.changed('append: %r', item)
    return super(TrackedList, self).append(self.convert(item, self))

  def extend(self, iterable):
    self.changed('extend: %r', iterable)
    return super(TrackedList, self).extend(
        self.convert_iterable(iterable, self))

  def pop(self, index):
    self.changed('pop: %d', index)
    return super(TrackedList, self).pop(index)
