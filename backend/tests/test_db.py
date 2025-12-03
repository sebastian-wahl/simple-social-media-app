# backend/tests/test_db.py
from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from social_media_app.db import (
    PostFilter,
    TagWithCount,
    add_comment_db,
    create_db_and_tables,
    create_post_db,
    get_post_db,
    list_comments_db,
    list_posts_db,
    list_tags_db,
)
from social_media_app.models import Post

# ---------------------------------------------------------------------------
# Test DB setup: shared in-memory SQLite per test function
# ---------------------------------------------------------------------------


def make_test_engine():
    """
    Create an in-memory SQLite engine that persists for the duration
    of a test (StaticPool keeps the same DB across sessions).
    """
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


@pytest.fixture
def session() -> Iterator[Session]:
    """
    Fresh in-memory DB per test.

    Uses the same create_db_and_tables() function as the real app,
    but with an in-memory engine instead of the file-based one.
    """
    engine = make_test_engine()
    create_db_and_tables(engine)
    with Session(engine) as s:
        yield s


# ---------------------------------------------------------------------------
# Tests for basic post creation / retrieval
# ---------------------------------------------------------------------------


def test_create_post_assigns_id_and_tags(session: Session):
    post = create_post_db(
        session,
        image_path="a.jpg",
        text="hello world",
        user="alice",
        toe_rating=5,
        tags=["test", "fun"],
    )

    assert post.id == 1
    assert post.image_path == "a.jpg"
    assert post.user == "alice"
    # tags relationship should be populated
    tag_names = sorted(t.name for t in post.tags)
    assert tag_names == ["fun", "test"]


def test_get_post_db_returns_none_for_missing(session: Session):
    # No posts yet
    assert get_post_db(session, 1) is None


def test_get_post_db_returns_post(session: Session):
    created = create_post_db(
        session,
        image_path="p.jpg",
        text="post",
        user="bob",
        toe_rating=3,
        tags=[],
    )

    fetched = get_post_db(session, created.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.text == "post"
    assert fetched.user == "bob"


# ---------------------------------------------------------------------------
# Tests for list_posts_db (ordering, pagination, filters)
# ---------------------------------------------------------------------------


def _seed_posts_for_list_tests(session: Session) -> list[Post]:
    """
    Helper to insert a few posts with different ratings and tags.
    """
    posts: list[Post] = []
    posts.append(
        create_post_db(
            session,
            image_path="1.jpg",
            text="first post",
            user="u1",
            toe_rating=3,
            tags=["blue", "common"],
        )
    )
    posts.append(
        create_post_db(
            session,
            image_path="2.jpg",
            text="second post",
            user="u2",
            toe_rating=5,
            tags=["red", "common"],
        )
    )
    posts.append(
        create_post_db(
            session,
            image_path="3.jpg",
            text="third post",
            user="u3",
            toe_rating=1,
            tags=["green"],
        )
    )
    return posts


def test_list_posts_basic_pagination(session: Session):
    _seed_posts_for_list_tests(session)

    f = PostFilter(limit=2, offset=0, order_by="newest")
    f_2 = PostFilter(limit=5, offset=0, order_by="newest")
    posts, total = list_posts_db(session, f)
    posts_2, total2 = list_posts_db(session, f_2)

    assert len(posts) == 2
    assert total == total2
    assert total == 3
    assert len(posts_2) == 3


def test_list_posts_filter_by_tag_any(session: Session):
    _seed_posts_for_list_tests(session)

    # Posts that have tag "common" (ANY semantics)
    f = PostFilter(tags=["common"], match_all=False)
    posts, total = list_posts_db(session, f)

    names = sorted(p.text for p in posts)
    assert total == 2
    assert names == ["first post", "second post"]


def test_list_posts_filter_by_min_rating(session: Session):
    _seed_posts_for_list_tests(session)

    # Only posts with rating >= 4
    f = PostFilter(min_rating=4, order_by="rating")
    posts, total = list_posts_db(session, f)

    assert total == 1
    assert len(posts) == 1
    assert posts[0].toe_rating == 5
    assert posts[0].text == "second post"


# ---------------------------------------------------------------------------
# Tests for list_tags_db
# ---------------------------------------------------------------------------


def test_list_tags_db_counts(session: Session):
    _seed_posts_for_list_tests(session)

    tags: list[TagWithCount] = list_tags_db(session)

    # Build dict {name: count} for easier assertions
    by_name = {t.name: t.count for t in tags}

    # "common" should appear twice, others once
    assert by_name["common"] == 2
    assert by_name["blue"] == 1
    assert by_name["red"] == 1
    assert by_name["green"] == 1


def test_list_comments_empty(session: Session):
    """No comments exist yet → empty list."""
    _seed_posts_for_list_tests(session)
    post = get_post_db(session, 1)  # type: ignore
    comments = list_comments_db(session, post.id)
    assert comments == []


def test_add_comment_creates_and_returns_comment(session: Session):
    """Check that a comment is inserted, given an existing post."""
    _seed_posts_for_list_tests(session)
    post = get_post_db(session, 1)  # type: ignore

    comment = add_comment_db(
        session,
        post_id=post.id,
        user="alice",
        text="Nice post!",
    )

    assert comment.id == 1
    assert comment.post_id == post.id
    assert comment.user == "alice"
    assert comment.text == "Nice post!"


# ---------------------------------------------------------------------------
# Tests for comments
# ---------------------------------------------------------------------------


def test_list_comments_ordering(session: Session):
    """
    Comments must be returned oldest-first (ASC created_at ordering).
    """
    _seed_posts_for_list_tests(session)
    post = get_post_db(session, 1)  # type: ignore

    c1 = add_comment_db(session, post_id=post.id, user="u1", text="First!")
    c2 = add_comment_db(session, post_id=post.id, user="u2", text="Second!")

    comments = list_comments_db(session, post.id)

    assert len(comments) == 2
    assert comments[0].id == c1.id
    assert comments[1].id == c2.id


def test_comments_separated_by_post(session: Session):
    """
    Comments must belong to their posts and not mix between posts.
    """
    _seed_posts_for_list_tests(session)

    p1 = get_post_db(session, 1)  # type: ignore
    p2 = get_post_db(session, 2)  # type: ignore

    add_comment_db(session, post_id=p1.id, user="u1", text="C1")
    add_comment_db(session, post_id=p2.id, user="u2", text="C2")

    comments_p1 = list_comments_db(session, p1.id)
    comments_p2 = list_comments_db(session, p2.id)

    assert len(comments_p1) == 1
    assert len(comments_p2) == 1

    assert comments_p1[0].text == "C1"
    assert comments_p2[0].text == "C2"
