# Third-party modules
try:
  import simplejson as json
except ImportError:
  import json

import sqlalchemy
from sqlalchemy.ext import mutable
from sqlalchemy_utils.types.json import JSONType

# Custom modules
from . import track


class NestedMutable(mutable.MutableDict, track.TrackedDict):
  """SQLAlchemy `mutable` extension dictionary with nested change tracking."""
  def __setitem__(self, key, value):
    """Ensure that items set are converted to change-tracking types."""
    super(NestedMutable, self).__setitem__(key, self.convert(value, self))

  @classmethod
  def coerce(cls, key, value):
    """Convert plain dictionary to NestedMutable."""
    if isinstance(value, cls):
      return value
    if isinstance(value, dict):
      return cls(value)
    return super(cls).coerce(key, value)


class JsonObject(JSONType):
  """JSON object type for SQLAlchemy with change tracking as base level."""


class NestedJsonObject(JSONType):
  """JSON object type for SQLAlchemy with nested change tracking."""


mutable.MutableDict.associate_with(JsonObject)
NestedMutable.associate_with(NestedJsonObject)
