from datetime import datetime, UTC

from sqlmodel import Field, Relationship, SQLModel

# Datetime factory
def utcnow() -> datetime:
    """Return an aware UTC datetime for default_factory."""
    return datetime.now(UTC)

# --- Link table: many-to-many between Post and Tag ---
class PostTagLink(SQLModel, table=True):
    __tablename__ = "post_tag_link"

    post_id: int | None = Field(default=None, foreign_key="post.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # Many-to-many: one tag can belong to many posts
    posts: list["Post"] = Relationship(
        back_populates="tags",
        link_model=PostTagLink,
    )


class Post(SQLModel, table=True):
    """
    Social post with MinIO object key in image_path.

    Ratings now live in a separate ToeRating table and are aggregated
    (mean) when reading posts.
    """

    id: int | None = Field(default=None, primary_key=True)
    image_path: str  # MinIO object key or path
    text: str
    user: str
    created_at: datetime = Field(default_factory=utcnow, index=True)

    # Many-to-many: one post can have many tags
    tags: list["Tag"] = Relationship(
        back_populates="posts",
        link_model=PostTagLink,
    )

    # one-to-many: a post can have many toe ratings
    ratings: list["ToeRating"] = Relationship(back_populates="post")


class Comment(SQLModel, table=True):
    """
    One-level (root) comments that belong to a single Post.
    """

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    user: str
    text: str
    created_at: datetime = Field(default_factory=utcnow, index=True)

    sentiment: str | None = Field(default=None, index=True)
    sentiment_score: float | None = None


class ToeRating(SQLModel, table=True):
    """
    Separate per-user toe rating for a post (1–5).
    The mean of these values is returned in PostReadDTO.toe_rating.
    """
    __tablename__ = "toe_rating"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    user: str
    value: int = Field(ge=1, le=5, description="Toe rating 1–5")
    created_at: datetime = Field(default_factory=utcnow, index=True)

    post: Post | None = Relationship(back_populates="ratings")
