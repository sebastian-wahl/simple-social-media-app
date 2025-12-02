from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field as PydField

from .config import settings
from .models import Comment, Post

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
    """

    image_path: str
    text: str
    user: str
    toe_rating: int = PydField(ge=1, le=5)
    tags: list[str] = []  # tag names


class PostReadDTO(BaseModel):
    id: int
    image_path: str
    image_url: str # full URL delivered to client
    text: str
    user: str
    toe_rating: int
    created_at: str
    tags: list[str]


class PostFilterDTO(BaseModel):
    """
    Filter object for /posts and /posts/search.

    API layer:
      - validates incoming query params
      - passes them as PostFilter to the DB layer.
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
    Map a Post SQLModel instance (with tags loaded) to PostReadDTO.
    """
    backend_url = settings.APP_HOST

    return PostReadDTO(
        id=post.id,
        image_path=post.image_path,
        image_url=f"{backend_url}/images/{post.image_path}",
        text=post.text,
        user=post.user,
        toe_rating=post.toe_rating,
        created_at=post.created_at.isoformat(),
        tags=[t.name for t in (post.tags or [])],
    )


def comment_to_dto(comment: Comment) -> CommentReadDTO:
    """
    Map a Comment SQLModel instance to CommentReadDTO.
    """
    return CommentReadDTO(
        id=comment.id,  # type: ignore[arg-type]
        post_id=comment.post_id,
        user=comment.user,
        text=comment.text,
        created_at=comment.created_at.isoformat(),
    )
