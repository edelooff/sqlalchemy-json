import copy
import pickle
import sys

import pytest

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy_json import (
    MutableJson,
    NestedMutableDict,
    NestedMutableJson,
    NestedMutableList,
)

SQLALCHEMY_DATABASE_URL = "sqlite://"
Base = declarative_base()


class Author(Base):
    __tablename__ = "author"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    handles = Column(MutableJson)


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    author = Column(ForeignKey("author.name"))
    content = Column(Text)
    references = Column(NestedMutableJson)


@pytest.fixture
def session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def author(session):
    author = Author(
        name="John Doe",
        handles={"twitter": "@JohnDoe", "facebook": "JohnDoe"},
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    assert author.name == "John Doe"
    assert author.handles["twitter"] == "@JohnDoe"
    return author

@pytest.fixture
def author_with_list(session):
    author = Author(
        name="John Doe",
        handles=["@JohnDoe", "JohnDoe"],
    )
    session.add(author)
    session.commit()
    session.refresh(author)

    assert author.name == "John Doe"
    assert author.handles == ["@JohnDoe", "JohnDoe"]
    return author

@pytest.fixture
def article(session, author):
    references = {
        "github.com": {
            "edelooff/sqlalchemy-json": 4,
            "zzzeek/sqlalchemy": [1, 2, 3],
        }
    }
    article = Article(
        author=author.name,
        content="very important",
        references=references,
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    assert article.references == references
    return article


def test_basic_change_tracking(session, author):
    author.handles["twitter"] = "@JDoe"
    session.commit()
    assert author.handles["twitter"] == "@JDoe"


def test_nested_change_tracking(session, article):
    article.references["github.com"]["edelooff/sqlalchemy-json"] = 5
    article.references["github.com"]["zzzeek/sqlalchemy"].append(4)
    session.commit()
    assert article.references["github.com"]["edelooff/sqlalchemy-json"] == 5
    assert article.references["github.com"]["zzzeek/sqlalchemy"] == [1, 2, 3, 4]


def test_nested_pickling():
    one = NestedMutableDict({"numbers": [1, 2, 3, {"4": 4}]})
    two = NestedMutableList([5, 6, 7, {"numbers": [8, 9, 10]}])

    # Force evaluation of _parents property
    one._parents
    two._parents

    one_reloaded = pickle.loads(pickle.dumps(one))
    two_reloaded = pickle.loads(pickle.dumps(two))
    assert one == one_reloaded
    assert two == two_reloaded

    one_reloaded["numbers"].append(5)
    assert one_reloaded["numbers"] == [1, 2, 3, {"4": 4}, 5]
    assert one["numbers"] == [1, 2, 3, {"4": 4}]
    assert one_reloaded["numbers"].parent is one_reloaded
    assert one_reloaded["numbers"][3].parent is one_reloaded["numbers"]

    two_reloaded.append(11)
    assert two_reloaded == [5, 6, 7, {"numbers": [8, 9, 10]}, 11]
    assert two == [5, 6, 7, {"numbers": [8, 9, 10]}]
    assert two_reloaded[3].parent is two_reloaded
    assert two_reloaded[3]["numbers"].parent is two_reloaded[3]


def test_deepcopy(session, article):
    """Modifying a copy of a MutableJSON instance does not affect the source."""
    new_repo = "someone/newrepo"
    assert new_repo not in article.references["github.com"]

    article_copy = Article(
        author=article.author,
        content=article.content,
        references=copy.deepcopy(article.references),
    )
    article_copy.references["github.com"][new_repo] = 10
    article_copy.references["modified"] = True

    assert new_repo not in article.references["github.com"]
    assert not session.dirty


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Python 3.9+ required")
def test_dict_merging(session, article):
    article.references["github.com"] |= {"someone/somerepo": 10}
    session.commit()
    assert article.references == {
        "github.com": {
            "edelooff/sqlalchemy-json": 4,
            "zzzeek/sqlalchemy": [1, 2, 3],
            "someone/somerepo": 10,
        },
    }

def test_mutable_json_list(session, author_with_list):
    author_with_list.handles.append("@mike_bianco")
    session.commit()

    assert author_with_list.handles == ["@JohnDoe", "JohnDoe", "@mike_bianco"]
    