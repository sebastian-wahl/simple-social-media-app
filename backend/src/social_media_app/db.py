# Add db connection here
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from .models import Post


# ToDo adapt later
def make_engine(sqlite_memory: bool = True):
    """
    Create an engine.
    - For tests: use an in-memory SQLite DB that persists across sessions
      by using a StaticPool.
    - For later (file DB): set sqlite_memory=False (writes app.db on disk).
    """
    if sqlite_memory:
        return create_engine(
            "sqlite://",  # in-memory
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine("sqlite:///app.db", echo=False)


def create_db_and_tables(engine) -> None:
    SQLModel.metadata.create_all(engine)


def add_post(session: Session, post: Post) -> int:
    session.add(post)
    session.commit()
    session.refresh(post)
    return int(post.id)  # type: ignore[arg-type]


def add_posts(session: Session, posts: Iterable[Post]) -> list[int]:
    for p in posts:
        session.add(p)
    session.commit()
    ids: list[int] = []
    for p in posts:
        session.refresh(p)
        ids.append(int(p.id))  # type: ignore[arg-type]
    return ids


def get_latest_post(session: Session) -> Post | None:
    stmt = select(Post).order_by(Post.created_at.desc()).limit(1)
    return session.exec(stmt).first()
