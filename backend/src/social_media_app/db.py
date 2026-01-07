from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session, SQLModel, create_engine, func, select

from .models import Comment, Post, PostTagLink, Tag

# ---------------------------
# Engine & Session
# ---------------------------


def make_engine():
    """
    Use DATABASE_URL (e.g. postgresql+psycopg://user:pass@db:5432/social-media-app)
    or fall back to a local SQLite file for development.
    """
    url = os.getenv("DATABASE_URL")  # ToDo add this once a db is implemented
    if url:
        return create_engine(url, echo=False, pool_pre_ping=True)

    # Dev/test default: SQLite file
    return create_engine("sqlite:///social-media-app.db", echo=False)


def get_session() -> Iterator[Session]:
    """
    FastAPI dependency: yields a Session per request.
    """
    engine = make_engine()
    with Session(engine) as session:
        yield session


# ---------------------------
# Filter & helper types
# ---------------------------


@dataclass
class PostFilter:
    q: str | None = None
    tags: list[str] | None = None
    match_all: bool = False
    # min_rating / max_rating apply to mean ToeRating.value
    min_rating: int | None = None
    max_rating: int | None = None
    limit: int = 20
    offset: int = 0
    order_by: str = "relevance"  # relevance | newest | rating


@dataclass
class TagWithCount:
    id: int
    name: str
    count: int


# ---------------------------
# Internal helpers (DB-level)
# ---------------------------


def _ensure_tags(session: Session, tag_names: list[str]) -> list[Tag]:
    """
    Get or create Tag rows for the given names and return them.
    """
    if not tag_names:
        return []

    existing = session.exec(select(Tag).where(Tag.name.in_(tag_names))).all()
    existing_names = {t.name for t in existing}

    to_create = [Tag(name=n) for n in tag_names if n not in existing_names]
    for t in to_create:
        session.add(t)

    if to_create:
        session.commit()
        for t in to_create:
            session.refresh(t)

    return existing + to_create


# ---------------------------
# DB operations: Posts
# ---------------------------


def create_post_db(
    session: Session,
    *,
    image_path: str,
    text: str,
    user: str,
    tags: list[str],
) -> Post:
    """
    Create a new Post with the given data and associated tags.

    toe_rating is no longer part of the Post.
    Ratings are created via add_rating_db() from the rating endpoint.
    """
    post = Post(
        image_path=image_path,
        text=text,
        user=user,
    )
    post.tags = _ensure_tags(session, tags)
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


def list_posts_db(session: Session, f: PostFilter) -> tuple[list[Post], int]:
    stmt = select(Post)

    # Search
    if f.q:
        stmt = stmt.where(
            (Post.text.ilike(f"%{f.q}%")) |
            (Post.user.ilike(f"%{f.q}%"))
        )

    # Tag filter
    if f.tags:
        stmt = (
            stmt
            .join(PostTagLink, PostTagLink.post_id == Post.id)
            .join(Tag, Tag.id == PostTagLink.tag_id)
            .where(Tag.name.in_(f.tags))
            .group_by(Post.id)
        )

        if f.match_all:
            stmt = stmt.having(
                func.count(func.distinct(Tag.id)) == len(f.tags)
            )

    # Rating filter (NOW works)
    if f.min_rating is not None:
        stmt = stmt.where(Post.rating >= f.min_rating)

    if f.max_rating is not None:
        stmt = stmt.where(Post.rating <= f.max_rating)

    # Ordering
    if f.order_by == "newest":
        stmt = stmt.order_by(Post.created_at.desc())
    elif f.order_by == "rating":
        stmt = stmt.order_by(Post.rating.desc(), Post.created_at.desc())
    else:
        stmt = stmt.order_by(Post.created_at.desc())

    total = session.exec(
        select(func.count()).select_from(stmt.subquery())
    ).one()

    posts = session.exec(
        stmt.offset(f.offset).limit(f.limit)
    ).all()

    return posts, total


def get_post_db(session: Session, post_id: int) -> Post | None:
    return session.get(Post, post_id)



# ---------------------------
# DB operations: Tags
# ---------------------------


def list_tags_db(session: Session) -> list[TagWithCount]:
    """
    Return tags and how many posts use each.
    """
    rows = session.exec(
        select(Tag.id, Tag.name, func.count(PostTagLink.post_id))
        .join(PostTagLink, PostTagLink.tag_id == Tag.id, isouter=True)
        .group_by(Tag.id, Tag.name)
        .order_by(Tag.name.asc())
    ).all()

    return [TagWithCount(id=row[0], name=row[1], count=row[2]) for row in rows]


# ---------------------------
# DB operations: Comments
# ---------------------------


def list_comments_db(session: Session, post_id: int) -> list[Comment]:
    return session.exec(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
    ).all()


def add_comment_db(
    session: Session,
    *,
    post_id: int,
    user: str,
    text: str,
) -> Comment:
    comment = Comment(post_id=post_id, user=user, text=text)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def create_db_and_tables(engine) -> None:
    """
    Only creates tables if they do not already exist
    """
    SQLModel.metadata.create_all(engine)
