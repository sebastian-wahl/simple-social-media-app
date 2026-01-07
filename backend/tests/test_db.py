from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from social_media_app.models import Post, Comment
from worker.sentiment_worker import recompute_post_rating


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_post_rating_no_comments():
    session = make_session()

    post = Post(image_path="posts/x.jpg", text="test", user="alice")
    session.add(post)
    session.commit()
    session.refresh(post)

    recompute_post_rating(session, post.id)
    session.refresh(post)

    assert post.rating == 0.0


def test_post_rating_single_positive_comment():
    session = make_session()

    post = Post(image_path="posts/x.jpg", text="test", user="alice")
    session.add(post)
    session.commit()
    session.refresh(post)

    comment = Comment(
        post_id=post.id,
        user="bob",
        text="Great!",
        sentiment="positive",
        sentiment_score=1.0,
    )
    session.add(comment)
    session.commit()

    recompute_post_rating(session, post.id)
    session.refresh(post)

    assert post.rating == 5.0


def test_post_rating_mixed_sentiment():
    session = make_session()

    post = Post(image_path="posts/x.jpg", text="test", user="alice")
    session.add(post)
    session.commit()
    session.refresh(post)

    comments = [
        Comment(
            post_id=post.id,
            user="u1",
            text="Nice",
            sentiment="positive",
            sentiment_score=1.0,
        ),
        Comment(
            post_id=post.id,
            user="u2",
            text="Meh",
            sentiment="neutral",
            sentiment_score=1.0,
        ),
        Comment(
            post_id=post.id,
            user="u3",
            text="Bad",
            sentiment="negative",
            sentiment_score=1.0,
        ),
    ]

    session.add_all(comments)
    session.commit()

    recompute_post_rating(session, post.id)
    session.refresh(post)

    assert 1.0 <= post.rating <= 5.0


def test_post_rating_ignores_unanalyzed_comments():
    session = make_session()

    post = Post(image_path="posts/x.jpg", text="test", user="alice")
    session.add(post)
    session.commit()
    session.refresh(post)

    comment = Comment(
        post_id=post.id,
        user="bob",
        text="Pending analysis",
        sentiment=None,
        sentiment_score=None,
    )
    session.add(comment)
    session.commit()

    recompute_post_rating(session, post.id)
    session.refresh(post)

    assert post.rating == 0.0
