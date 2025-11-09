# unit tests for db layer
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from social_media_app.db import (
    add_post,
    add_posts,
    create_db_and_tables,
    get_latest_post,
    make_engine,
)
from social_media_app.models import Post


@pytest.fixture
def session():
    # Fresh in-memory DB per test
    engine = make_engine(sqlite_memory=True)
    create_db_and_tables(engine)
    with Session(engine) as s:
        yield s


def test_add_and_get_latest(session: Session):
    now = datetime(2024, 1, 1, 12, 0, 0)
    posts = [
        Post(image_path="a.jpg", text="first", user="alice", created_at=now - timedelta(minutes=2)),
        Post(image_path="b.jpg", text="second", user="bob", created_at=now - timedelta(minutes=1)),
        Post(image_path="c.jpg", text="third", user="carol", created_at=now),
    ]
    ids = add_posts(session, posts)
    assert ids == [1, 2, 3]

    latest = get_latest_post(session)
    assert latest is not None
    assert latest.id == 3
    assert latest.text == "third"
    assert latest.user == "carol"


def test_empty_repo_returns_none(session: Session):
    # Fresh DB -> no rows
    assert get_latest_post(session) is None


def test_auto_increment_ids(session: Session):
    base = datetime(2024, 1, 1)
    id1 = add_post(session, Post(image_path="x.jpg", text="t1", user="u", created_at=base))
    id2 = add_post(session, Post(image_path="y.jpg", text="t2", user="u", created_at=base))
    assert (id1, id2) == (1, 2)
