from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session, SQLModel, create_engine, func, select

from .models import Comment, Post, PostTagLink, Tag, ToeRating

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


def _avg_rating_for_post(post: Post) -> float | None:
    """
    Helper to compute the average rating for a Post in Python.

    NOTE: This uses the Post.ratings relationship. For small datasets this
    is fine; for larger ones you might want to push aggregation into SQL.
    """
    ratings = getattr(post, "ratings", []) or []
    if not ratings:
        return None
    return sum(r.value for r in ratings) / len(ratings)


def list_posts_db(session: Session, f: PostFilter) -> tuple[list[Post], int]:
    """
    Return a (posts, total_count) tuple based on the given filter.

    - All rating logic (min_rating/max_rating and rating/relevance
      ordering) uses the mean of ToeRating.value via
      _avg_rating_for_post().
    - Implemented in Python for simplicity (fine for this project).
    """
    stmt = select(Post)

    # Search
    if f.q:
        stmt = stmt.where((Post.text.ilike(f"%{f.q}%")) | (Post.user.ilike(f"%{f.q}%")))

    # Tag filter (unchanged)
    if f.tags:
        if f.match_all:
            # Posts containing ALL requested tags
            stmt = (
                select(Post)
                .join(PostTagLink, PostTagLink.post_id == Post.id)
                .join(Tag, Tag.id == PostTagLink.tag_id)
                .where(Tag.name.in_(f.tags))
                .group_by(Post.id)
                .having(func.count(func.distinct(Tag.id)) == len(f.tags))
            )
        else:
            # Posts containing ANY of the requested tags
            stmt = (
                select(Post)
                .join(PostTagLink, PostTagLink.post_id == Post.id)
                .join(Tag, Tag.id == PostTagLink.tag_id)
                .where(Tag.name.in_(f.tags))
                .group_by(Post.id)
            )

    # Execute base query (without rating-dependent limit/offset/order)
    posts: list[Post] = session.exec(stmt).all()

    # Rating-based filtering (mean of ToeRating.value)
    if f.min_rating is not None:
        posts = [
            p
            for p in posts
            if _avg_rating_for_post(p) is not None and _avg_rating_for_post(p) >= f.min_rating
        ]

    if f.max_rating is not None:
        posts = [
            p
            for p in posts
            if _avg_rating_for_post(p) is not None and _avg_rating_for_post(p) <= f.max_rating
        ]

    # Ordering
    if f.order_by == "newest":
        posts.sort(key=lambda p: p.created_at, reverse=True)
    else:
        # "rating" and "relevance": sort by mean rating then recency
        posts.sort(
            key=lambda p: (_avg_rating_for_post(p) or 0.0, p.created_at),
            reverse=True,
        )

    total = len(posts)

    # Pagination
    posts = posts[f.offset : f.offset + f.limit]

    return posts, total


def get_post_db(session: Session, post_id: int) -> Post | None:
    return session.get(Post, post_id)


# ---------------------------
# DB operations: Ratings
# ---------------------------


def add_or_update_rating_db(
    session: Session,
    *,
    post_id: int,
    user: str,
    value: int,
) -> ToeRating:
    """
    Create or update a toe rating for a post.
      - If a rating for (post_id, user) already exists, its value (and
        timestamp) are updated instead of inserting a second row.
      - This gives the semantics: "second time overwrites the first rating".
    """
    existing = session.exec(
        select(ToeRating).where(
            ToeRating.post_id == post_id,
            ToeRating.user == user,
        )
    ).first()

    if existing:
        existing.value = value
        existing.created_at = datetime.now(UTC)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    rating = ToeRating(post_id=post_id, user=user, value=value)
    session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating


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
