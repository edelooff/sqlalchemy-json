sqlalchemy-json
###############

SQLAlchemy-JSON provides mutation-tracked JSON types to SQLAlchemy_:

* ``MutableJson`` is a straightforward implementation for keeping track of top-level changes to JSON objects;
* ``NestedMutableJson`` is an extension of this which tracks changes even when these happen in nested objects or arrays (Python ``dicts`` and ``lists``).


Examples
========

Basic change tracking
---------------------

This is essentially the SQLAlchemy `mutable JSON recipe`_. We define a simple author model which list the author's name and a property ``handles`` for various social media handles used:

.. code-block:: python

    class Author(Base):
        name = Column(Text)
        handles = Column(MutableJson)

The example below loads one of the existing authors and retrieves the mapping of social media handles. The error in the twitter handle is then corrected and committed. The change is detected by SQLAlchemy and the appropriate ``UPDATE`` statement is generated.

.. code-block:: python

    >>> author = session.query(Author).first()
    >>> author.handles
    {'twitter': '@JohnDoe', 'facebook': 'JohnDoe'}
    >>> author.handles['twitter'] = '@JDoe'
    >>> session.commit()
    >>> author.handles
    {'twitter': '@JDoe', 'facebook': 'JohnDoe'}


Nested change tracking
----------------------

The example below defines a simple model for articles. One of the properties on this model is a mutable JSON structure called ``references`` which includes a count of links that the article contains, grouped by domain:

.. code-block:: python

    class Article(Base):
        author = Column(ForeignKey('author.name'))
        content = Column(Text)
        references = Column(NestedMutableJson)

With this in place, an existing article is loaded and its current references inspected. Following that, the count for one of these is increased by ten, and the session is committed:

.. code-block:: python

    >>> article = session.query(Article).first()
    >>> article.references
    {'github.com': {'edelooff/sqlalchemy-json': 4, 'zzzeek/sqlalchemy': 7}}
    >>> article.references['github.com']['edelooff/sqlalchemy-json'] += 10
    >>> session.commit()
    >>> article.references
    {'github.com': {'edelooff/sqlalchemy-json': 14, 'zzzeek/sqlalchemy': 7}}

Had the articles model used ``MutableJson`` like in the previous example this code would have failed. This is because the top level dictionary is never altered directly. The *nested* mutable ensures the change happening at the lower level *bubbles up* to the outermost container.


Non-native JSON / other serialization types
===========================================

By default, sqlalchemy-json uses the JSON column type provided by SQLAlchemy (specifically ``sqlalchemy.types.JSON``.)
If you wish to use another type (e.g. PostgreSQL's ``JSONB``), your database does not natively support JSON (e.g. SQLite), or you wish to serialize to a format other than JSON, you'll need to provide a different backing type.

This is done by using the utility function ``mutable_json_type``. This type creator function accepts two parameters:

* ``dbtype`` controls the database type used. This can be an existing type provided by SQLAlchemy or SQLALchemy-utils_, or an `augmented type`_ to provide serialization to any other format;
* ``nested`` controls whether the created type is made mutable based on ``MutableDict`` or ``NestedMutable`` (defaults to ``False`` for ``MutableDict``).


Dependencies
============

* ``six`` to support both Python 2 and 3.


Changelog
=========

0.4.0
-----

* Adds a type creation function to allow for custom or alternate serialization types. This allows for a way around the regression in SQLite compatibility introduced by v0.3.0.

0.3.0
-----

* Switches JSON base type to ``sqlalchemy.types.JSON`` from deprecated JSON type provided by SQLAlchemy-utils.

0.2.2
-----

* Fixes a bug where assigning ``None`` to the column resulted in an error (https://github.com/edelooff/sqlalchemy-json/issues/10)


0.2.1
-----

* Fixes a typo in the README found after uploading 0.2.0 to PyPI.


0.2.0 (unreleased)
------------------

* Now uses ``JSONType`` provided by SQLAlchemy-utils_ to handle backend storage;
* **Backwards incompatible**: Changed class name ``JsonObject`` to ``MutableJson`` and ``NestedJsonObject`` to ``NestedMutableJson``
* Outermost container for ``NestedMutableJson`` can now be an ``array`` (Python ``list``)


0.1.0 (unreleased)
------------------

Initial version. This initially carried a 1.0.0 version number but has never been released on PyPI.


.. _augmented type: https://docs.sqlalchemy.org/en/13/core/custom_types.html#augmenting-existing-types
.. _mutable json recipe: http://docs.sqlalchemy.org/en/latest/core/custom_types.html#marshal-json-strings
.. _sqlalchemy: https://www.sqlalchemy.org/
.. _sqlalchemy-utils: https://sqlalchemy-utils.readthedocs.io/
