import json
from types import SimpleNamespace

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from worker import sentiment_worker
from social_media_app.models import Comment


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_update_comment_sentiment(session):
    comment = Comment(post_id=1, user="bob", text="Nice!")
    session.add(comment)
    session.commit()
    session.refresh(comment)

    sentiment_worker.update_comment_sentiment(
        session,
        comment_id=comment.id,
        sentiment="POSITIVE",
        score=0.99,
    )

    session.refresh(comment)
    assert comment.sentiment == "POSITIVE"
    assert comment.sentiment_score == 0.99


def test_callback_processes_message(monkeypatch, session):
    # Fake model
    monkeypatch.setattr(
        sentiment_worker,
        "analyze_sentiment",
        lambda text: ("NEGATIVE", 0.12),
    )

    # Fake DB engine
    monkeypatch.setattr(
        sentiment_worker,
        "engine",
        session.get_bind(),
    )

    comment = Comment(post_id=1, user="alice", text="Bad post")
    session.add(comment)
    session.commit()
    session.refresh(comment)

    body = json.dumps({
        "comment_id": comment.id,
        "text": comment.text,
    })

    ch = SimpleNamespace(
        basic_ack=lambda delivery_tag: None,
        basic_nack=lambda delivery_tag, requeue=False: None,
    )
    method = SimpleNamespace(delivery_tag=1)

    sentiment_worker.callback(ch, method, None, body)

    session.refresh(comment)
    assert comment.sentiment == "NEGATIVE"
    assert comment.sentiment_score == 0.12
