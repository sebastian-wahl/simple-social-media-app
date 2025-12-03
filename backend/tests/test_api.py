from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from social_media_app.app import app
from social_media_app.db import create_db_and_tables, get_session

# ---------------------------------------------------------------------------
# Test app + DB setup
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
def client(monkeypatch) -> Iterator[TestClient]:
    """
    FastAPI TestClient with:

    - In-memory SQLite DB
    - get_session overridden to use that DB
    - MinIO existence check mocked to always return True
      (so POST /posts doesn't require a real MinIO instance)
    """
    engine = make_test_engine()
    create_db_and_tables(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    # Override DB dependency
    app.dependency_overrides[get_session] = override_get_session

    # Mock MinIO existence check
    monkeypatch.setattr(
        "social_media_app.app.image_exists_in_minio",
        lambda image_path: True,
    )

    with TestClient(app) as c:
        yield c

    # Clean up overrides after tests
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Basic health check
# ---------------------------------------------------------------------------


def test_health_ok(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


# ---------------------------------------------------------------------------
# Posts: create, get, list, search
# ---------------------------------------------------------------------------


def _create_post_via_api(client: TestClient, **overrides) -> dict:
    payload = {
        "image_path": "posts/test.jpg",
        "text": "hello world",
        "user": "alice",
        "toe_rating": 5,
        "tags": ["blue", "common"],
    }
    payload.update(overrides)

    res = client.post("/posts", json=payload)
    assert res.status_code == 201
    return res.json()


def test_create_and_get_post(client: TestClient):
    created = _create_post_via_api(client)

    # Response should contain an ID and echo the fields
    assert created["id"] == 1
    assert created["image_path"] == "posts/test.jpg"
    assert created["user"] == "alice"
    assert created["toe_rating"] == 5
    assert sorted(created["tags"]) == ["blue", "common"]

    # GET /posts/{id}
    res = client.get(f"/posts/{created['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == created["id"]
    assert fetched["text"] == "hello world"


def test_list_posts_pagination_and_meta(client: TestClient):
    # Create a few posts
    _create_post_via_api(client, text="p1")
    _create_post_via_api(client, text="p2")
    _create_post_via_api(client, text="p3")

    res = client.get("/posts", params={"limit": 2, "offset": 0})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data and "meta" in data
    assert len(data["items"]) == 2
    assert data["meta"]["total"] == 3
    assert data["meta"]["limit"] == 2
    assert data["meta"]["offset"] == 0


def test_list_posts_without_q_returns_all(client: TestClient):
    _create_post_via_api(client, text="kittens and puppies")
    _create_post_via_api(client, text="only puppies here")

    res = client.get("/posts")  # no q parameter
    assert res.status_code == 200

    data = res.json()
    assert data["meta"]["total"] == 2
    texts = {item["text"] for item in data["items"]}
    assert texts == {"kittens and puppies", "only puppies here"}


def test_search_posts_by_text(client: TestClient):
    _create_post_via_api(client, text="kittens and puppies")
    _create_post_via_api(client, text="only puppies here")
    _create_post_via_api(client, text="nothing relevant")

    # use the main list endpoint with q as a filter
    res = client.get("/posts", params={"q": "kittens"})
    assert res.status_code == 200

    data = res.json()
    # Only the first post should match
    assert data["meta"]["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["text"] == "kittens and puppies"


def test_list_posts_filter_by_tag(client: TestClient):
    _create_post_via_api(client, text="blue one", tags=["blue"])
    _create_post_via_api(client, text="red one", tags=["red"])
    _create_post_via_api(client, text="both", tags=["blue", "red"])

    res = client.get("/posts", params={"tags": ["blue"]})
    assert res.status_code == 200
    data = res.json()
    texts = sorted(item["text"] for item in data["items"])

    # we check if the blue posts are in the results
    assert len(texts) == 2
    assert "blue one" in texts
    assert "both" in texts


# ---------------------------------------------------------------------------
# Comments endpoints
# ---------------------------------------------------------------------------


def test_add_and_list_comments(client: TestClient):
    post = _create_post_via_api(client)

    # No comments yet
    res = client.get(f"/posts/{post['id']}/comments")
    assert res.status_code == 200
    assert res.json() == []

    # Add comment
    res = client.post(
        f"/posts/{post['id']}/comments",
        json={"user": "bob", "text": "Nice post!"},
    )
    assert res.status_code == 201
    comment = res.json()
    assert comment["id"] == 1
    assert comment["post_id"] == post["id"]
    assert comment["user"] == "bob"
    assert comment["text"] == "Nice post!"

    # List comments again
    res = client.get(f"/posts/{post['id']}/comments")
    assert res.status_code == 200
    comments = res.json()
    assert len(comments) == 1
    assert comments[0]["text"] == "Nice post!"


def test_comment_endpoints_404_for_missing_post(client: TestClient):
    # Comments list on non-existing post
    res = client.get("/posts/999/comments")
    assert res.status_code == 404

    # Add comment to non-existing post
    res = client.post(
        "/posts/999/comments",
        json={"user": "bob", "text": "Hello"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Tags endpoint
# ---------------------------------------------------------------------------


def test_list_tags_counts(client: TestClient):
    _create_post_via_api(client, tags=["blue", "common"])
    _create_post_via_api(client, tags=["red", "common"])

    res = client.get("/tags")
    assert res.status_code == 200
    tags = res.json()

    by_name = {t["name"]: t["count"] for t in tags}
    assert by_name["common"] == 2
    assert by_name["blue"] == 1
    assert by_name["red"] == 1
