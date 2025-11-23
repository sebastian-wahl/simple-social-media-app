from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


# --- Link table: many-to-many between Post and Tag ---
class PostTagLink(SQLModel, table=True):
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
    Social post with MinIO object key in image_path and a 1–5 toe rating.
    """

    id: int | None = Field(default=None, primary_key=True)
    image_path: str  # MinIO object key or path
    text: str
    user: str
    toe_rating: int = Field(ge=1, le=5, description="Toe rating 1–5")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Many-to-many: one post can have many tags
    tags: list["Tag"] = Relationship(
        back_populates="posts",
        link_model=PostTagLink,
    )


class Comment(SQLModel, table=True):
    """
    One-level (root) comments that belong to a single Post.
    """

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    user: str
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
