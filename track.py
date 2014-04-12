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

  def _repr(self):
    """Object representation that includes the memory address."""
    return '<%(namespace)s.%(type)s object at 0x%(address)0xd>' % {
        'namespace': __name__,
        'type': type(self).__name__,
        'address': id(self)}

  def _track(self, value):
    """Convencience method to call `convert_to_tracked` for a given value."""
    return convert_to_tracked(value, self)

  def _track_iterable(self, iterable):
    """Returns a generator that performs `_track` on every of its members."""
    return (self._track(item) for item in iterable)

  def _track_iteritems(self, iteritems):
    """Returns a generator like `_track_iterable` for 2-tuple item-iterators."""
    return ((key, self._track(value)) for key, value in iteritems)

  def _track_mapping(self, mapping):
    """Convenience method to track either a dict or a 2-tuple iterator."""
    if isinstance(mapping, dict):
      return self._track_iteritems(mapping.iteritems())
    return self._track_iteritems(mapping)


class TrackedDict(TrackedObject, dict):
  """A TrackedObject implementation of the basic dictionary."""
  def __init__(self, source=(), **kwds):
    super(TrackedDict, self).__init__(itertools.chain(
        self._track_mapping(source),
        self._track_mapping(kwds)))

  def __setitem__(self, key, value):
    self.changed('__setitem__: %r=%r', key, value)
    return super(TrackedDict, self).__setitem__(key, self._track(value))

  def __delitem__(self, key):
    self.changed('__delitem__: %r', key)
    return super(TrackedDict, self).__delitem__(key)

  def update(self, source=(), **kwds):
    self.changed('update(%r, %r)', source, kwds)
    super(TrackedDict, self).update(itertools.chain(
        self._track_mapping(source),
        self._track_mapping(kwds)))


class TrackedList(TrackedObject, list):
  """A TrackedObject implementation of the basic list."""
  def __init__(self, iterable=()):
    super(TrackedList, self).__init__(self._track_iterable(iterable))

  def __setitem__(self, key, value):
    self.changed('__setitem__: %r=%r', key, value)
    return super(TrackedList, self).__setitem__(key, self._track(value))

  def __delitem__(self, key):
    self.changed('__delitem__: %r', key)
    return super(TrackedList, self).__delitem__(key)

  def append(self, item):
    self.changed('append: %r', item)
    return super(TrackedList, self).append(self._track(item))

  def extend(self, iterable):
    self.changed('extend: %r', iterable)
    return super(TrackedList, self).extend(self._track_iterable(iterable))

  def pop(self, index):
    self.changed('pop: %d', index)
    return super(TrackedList, self).pop(index)


def convert_to_tracked(obj, parent):
  """Converts dictionaries and lists to TrackedDict and TrackedList types.
  
  This allows the new structure to track changes at arbitrary levels of nesting.
  """
  if type(obj) == dict:
    obj = TrackedDict(obj)
    obj.parent = parent
  elif type(obj) == list:
    obj = TrackedList(obj)
    obj.parent = parent
  return obj
