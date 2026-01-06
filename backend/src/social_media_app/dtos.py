from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field as PydField

from .config import settings
from .models import Comment, Post  # CHANGED: ToeRating is used via Post.ratings only

# =============================================================================
# DTOs (API Input/Output)
# =============================================================================


class PostCreateDTO(BaseModel):
    """
    Data Transfer Object for creating a new Post.

    NOTE: image_path is NOT the raw image data.
    It is a key/path pointing to the image in MinIO.

    Typical flow:
      1) Client uploads image to /uploads/images (multipart)
         -> receives {"image_path": "posts/<uuid>.jpg"}
      2) Client calls POST /posts with that image_path + other fields.

    CHANGED: toe_rating was removed from the create payload.
    Rating is now done via a separate /posts/{post_id}/rating endpoint.
    """

    image_path: str
    text: str
    user: str
    tags: list[str] = []  # tag names


class PostReadDTO(BaseModel):
    id: int
    image_path: str
    image_url: str  # full URL delivered to client
    thumbnail_url: str | None
    text: str
    user: str
    # CHANGED: toe_rating is now the mean rating (float) and may be None if no ratings yet.
    toe_rating: float | None
    created_at: str
    tags: list[str]


class PostFilterDTO(BaseModel):
    """
    Filter object for /posts and /posts/search.

    API layer:
      - validates incoming query params
      - passes them as PostFilter to the DB layer.

    CHANGED: min_rating / max_rating still exist but now filter
    by the mean rating (ToeRating.value) instead of a column on Post.
    """

    q: str | None = None
    tags: list[str] | None = None
    match_all: bool = False
    min_rating: int | None = PydField(default=None, ge=1, le=5)
    max_rating: int | None = PydField(default=None, ge=1, le=5)
    limit: int = PydField(default=20, ge=1, le=100)
    offset: int = PydField(default=0, ge=0)
    order_by: str = "relevance"  # relevance | newest | rating


class CommentCreateDTO(BaseModel):
    user: str
    text: str


class CommentReadDTO(BaseModel):
    id: int
    post_id: int
    user: str
    text: str
    created_at: str

    sentiment: str | None = None
    sentiment_score: float | None = None


# NEW: DTO for rating a post ------------------------------------------
class ToeRatingCreateDTO(BaseModel):
    """
    DTO for rate endpoint.
    The "user" is stored so that later it can be used to
    prevent multiple ratings per user (if desired).
    """

    user: str
    toe_rating: int = PydField(ge=1, le=5)


class PageMetaDTO(BaseModel):
    total: int
    limit: int
    offset: int


class PostPageDTO(BaseModel):
    items: list[PostReadDTO]
    meta: PageMetaDTO


class TagReadDTO(BaseModel):
    id: int
    name: str
    count: int


class UploadImageResponseDTO(BaseModel):
    """
    Response DTO for /uploads/images.

    image_path is exactly what the client should pass to PostCreateDTO.image_path.
    """

    image_path: str


# =============================================================================
# Mapping helpers (DB model -> DTO)
# =============================================================================


def post_to_dto(post: Post) -> PostReadDTO:
    """
    Map a Post SQLModel instance (with tags & ratings loaded) to PostReadDTO.
    """
    # ✅ GEÄNDERT: Relative URLs, damit der Browser sie über den Proxy aufrufen kann
    ratings = getattr(post, "ratings", []) or []
    if ratings:
        avg_rating = sum(r.value for r in ratings) / len(ratings)
    else:
        avg_rating = 0.0

    # Thumbnail path
    thumbnail_path = post.image_path.replace("posts/", "thumbs/", 1)
    
    return PostReadDTO(
        id=post.id,
        image_path=post.image_path,
        image_url=post.image_path, 
        thumbnail_url=thumbnail_path, 
        text=post.text,
        user=post.user,
        toe_rating=avg_rating,
        created_at=post.created_at.isoformat(),
        tags=[t.name for t in (post.tags or [])],
    )



def comment_to_dto(comment: Comment) -> CommentReadDTO:
    """
    Map a Comment SQLModel instance to CommentReadDTO.
    """
    return CommentReadDTO(
        id=comment.id,
        post_id=comment.post_id,
        user=comment.user,
        text=comment.text,
        created_at=comment.created_at.isoformat(),
        sentiment=comment.sentiment,
        sentiment_score=comment.sentiment_score,
    )
