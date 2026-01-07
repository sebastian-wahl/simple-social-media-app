from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from social_media_app.app import app
from social_media_app.db import create_db_and_tables, get_session
from social_media_app.models import Comment
from worker.sentiment_worker import recompute_post_rating


# ---------------------------------------------------------------------------
# Test app + DB setup
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    engine = make_test_engine()
    create_db_and_tables(engine)
    return engine

def make_test_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


@pytest.fixture
def client(monkeypatch, engine) -> Iterator[TestClient]:
    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    monkeypatch.setattr(
        "social_media_app.app.image_exists_in_minio",
        lambda *_: True,
    )
    monkeypatch.setattr(
        "social_media_app.app.queue_service.publish",
        lambda *_, **__: None,
    )

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_ok(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_post_via_api(client: TestClient, **overrides) -> dict:
    payload = {
        "image_path": "posts/test.jpg",
        "text": "hello world",
        "user": "alice",
        "tags": ["blue", "common"],
    }
    payload.update(overrides)

    res = client.post("/posts", json=payload)
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

def test_create_and_get_post(client: TestClient):
    created = _create_post_via_api(client)

    assert created["id"] == 1
    assert created["rating"] == 0.0
    assert sorted(created["tags"]) == ["blue", "common"]

    res = client.get(f"/posts/{created['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["rating"] == 0.0


def test_list_posts_pagination_and_meta(client: TestClient):
    _create_post_via_api(client, text="p1")
    _create_post_via_api(client, text="p2")
    _create_post_via_api(client, text="p3")

    res = client.get("/posts", params={"limit": 2, "offset": 0})
    data = res.json()

    assert len(data["items"]) == 2
    assert data["meta"]["total"] == 3


def test_search_posts_by_text(client: TestClient):
    _create_post_via_api(client, text="kittens and puppies")
    _create_post_via_api(client, text="only puppies here")
    _create_post_via_api(client, text="nothing relevant")

    res = client.get("/posts", params={"q": "kittens"})
    data = res.json()

    assert data["meta"]["total"] == 1
    assert data["items"][0]["text"] == "kittens and puppies"


def test_list_posts_filter_by_tag(client: TestClient):
    _create_post_via_api(client, text="blue one", tags=["blue"])
    _create_post_via_api(client, text="red one", tags=["red"])
    _create_post_via_api(client, text="both", tags=["blue", "red"])

    res = client.get("/posts", params={"tags": ["blue"]})
    data = res.json()

    texts = {item["text"] for item in data["items"]}
    assert texts == {"blue one", "both"}


# ---------------------------------------------------------------------------
# Comments + sentiment-driven rating
# ---------------------------------------------------------------------------

def test_comment_updates_post_rating(client: TestClient, engine):
    post = _create_post_via_api(client)

    res = client.post(
        f"/posts/{post['id']}/comments",
        json={"user": "bob", "text": "Amazing post"},
    )
    assert res.status_code == 201

    with Session(engine) as session:
        comment = session.exec(select(Comment)).first()
        comment.sentiment = "positive"
        comment.sentiment_score = 1.0
        session.commit()

        recompute_post_rating(session, post["id"])

    res = client.get(f"/posts/{post['id']}")
    assert res.status_code == 200
    assert res.json()["rating"] == 5.0



def test_rating_filtering(client: TestClient, engine):
    low = _create_post_via_api(client, text="bad")
    high = _create_post_via_api(client, text="good")

    with Session(engine) as session:
        session.add_all([
            Comment(
                post_id=low["id"],
                user="x",
                text="terrible",
                sentiment="negative",
                sentiment_score=1.0,
            ),
            Comment(
                post_id=high["id"],
                user="y",
                text="great",
                sentiment="positive",
                sentiment_score=1.0,
            ),
        ])
        session.commit()

        recompute_post_rating(session, low["id"])
        recompute_post_rating(session, high["id"])

    res = client.get("/posts", params={"min_rating": 4})
    ids = {p["id"] for p in res.json()["items"]}

    assert high["id"] in ids
    assert low["id"] not in ids



# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def test_list_tags_counts(client: TestClient):
    _create_post_via_api(client, tags=["blue", "common"])
    _create_post_via_api(client, tags=["red", "common"])

    res = client.get("/tags")
    tags = res.json()

    by_name = {t["name"]: t["count"] for t in tags}
    assert by_name["common"] == 2
    assert by_name["blue"] == 1
    assert by_name["red"] == 1
