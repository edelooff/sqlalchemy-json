from sqlalchemy.ext.mutable import Mutable, MutableDict, MutableList
from sqlalchemy.types import JSON

from .track import TrackedDict, TrackedList

__all__ = "MutableJson", "NestedMutableJson", "mutable_json_type"
__version__ = "0.7.0"


class _PickleMixin:
    def __getstate__(self):
        d = self.__dict__.copy()
        d.pop("_parents", None)
        return d


class MutableContainer(Mutable):
    """SQLAlchemy `mutable` extension with single-level change tracking list or dict."""

    @classmethod
    def coerce(cls, key, value):
        if value is None:
            return value
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return MutableDict.coerce(key, value)
        if isinstance(value, list):
            return MutableList.coerce(key, value)
        return super(cls).coerce(key, value)


class NestedMutableDict(TrackedDict, Mutable, _PickleMixin):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(value)
        return super(cls).coerce(key, value)


class NestedMutableList(TrackedList, Mutable, _PickleMixin):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, list):
            return cls(value)
        return super(cls).coerce(key, value)


class NestedMutableContainer(Mutable):
    """SQLAlchemy `mutable` extension with nested change tracking."""

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to NestedMutableContainer."""
        if value is None:
            return value
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return NestedMutableDict.coerce(key, value)
        if isinstance(value, list):
            return NestedMutableList.coerce(key, value)
        return super(cls).coerce(key, value)


def mutable_json_type(dbtype=JSON, nested=False):
    """Type creator for (optionally nested) mutable JSON column types.

    The default backend data type is sqlalchemy.types.JSON, but can be set to
    any other type by providing the `dbtype` parameter.
    """
    mutable_type = NestedMutableContainer if nested else MutableContainer
    return mutable_type.as_mutable(dbtype)


# Base mutable JSON types
MutableJson = mutable_json_type()
NestedMutableJson = mutable_json_type(nested=True)
