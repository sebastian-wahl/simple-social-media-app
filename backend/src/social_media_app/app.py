# Main backend api entry point
from __future__ import annotations

from contextlib import asynccontextmanager
from mimetypes import guess_type

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from starlette.responses import StreamingResponse

from .db import (
    PostFilter,
    add_comment_db,
    create_db_and_tables,
    create_post_db,
    get_post_db,
    get_session,
    list_comments_db,
    list_posts_db,
    list_tags_db,
    make_engine,
)
from .dtos import (
    CommentCreateDTO,
    CommentReadDTO,
    PageMetaDTO,
    PostCreateDTO,
    PostFilterDTO,
    PostPageDTO,
    PostReadDTO,
    TagReadDTO,
    UploadImageResponseDTO,
    comment_to_dto,
    post_to_dto,
)
from .minio_db import get_image_bytes_from_minio, image_exists_in_minio, upload_image_to_minio

# =============================================================================
# Lifespan (startup/shutdown): create DB schema once at startup
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown lifecycle.

    - If using SQLite → create tables automatically (dev mode)
    - If using Postgres → do NOT auto-create tables (use migrations instead)
    """
    engine = make_engine()

    # Detect SQLite (filename-based or sqlite://)
    if engine.url.database is None or engine.url.drivername.startswith("sqlite"):
        print("Using SQLite — auto-creating tables")
        create_db_and_tables(engine)
    else:
        # for postgres this should be done via insert script and docker compose
        print("Using Postgres — skipping auto-create")
    engine = make_engine()
    create_db_and_tables(engine)
    yield


app = FastAPI(title="Social Media API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Routes: Image Upload (MinIO)
# =============================================================================


@app.post(
    "/uploads/images",
    response_model=UploadImageResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(file: UploadFile = File(...)):
    """
    Upload a single image to MinIO and return the generated image_path.
    Usage:
      1) Client sends multipart/form-data with the binary image.
      2) Backend:
         - generates a unique key for db storage (e.g. "posts/<uuid>.jpg")
         - uploads the bytes to MinIO into the configured bucket
         - returns that key as image_path
      3) Client uses this image_path when creating a post via POST /posts.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image uploads are allowed.",
        )

    try:
        image_path = upload_image_to_minio(file)
    except RuntimeError as exc:
        # Translate storage failure into 500 for the HTTP client
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return UploadImageResponseDTO(image_path=image_path)

@app.get("/images/{image_path:path}")
def get_image(image_path: str):
    """
    Return raw image bytes stored in MinIO.

    image_path is a key such as "posts/<uuid>.jpg".
    """
    try:
        data = get_image_bytes_from_minio(image_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    content_type, _ = guess_type(image_path)
    content_type = content_type or "application/octet-stream"

    return StreamingResponse(
        content=iter([data]),
        media_type=content_type,
    )

# =============================================================================
# Routes: Posts
# =============================================================================


@app.post("/posts", response_model=PostReadDTO, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateDTO, session: Session = Depends(get_session)):
    # new validation:
    if not image_exists_in_minio(payload.image_path):
        raise HTTPException(
            status_code=400, detail=f"Image does not exist in MinIO: {payload.image_path}"
        )

    post = create_post_db(
        session,
        image_path=payload.image_path,
        text=payload.text,
        user=payload.user,
        toe_rating=payload.toe_rating,
        tags=payload.tags,
    )
    return post_to_dto(post)


@app.get("/posts", response_model=PostPageDTO)
def list_posts(
    filter_dto: PostFilterDTO = Query(),
    session: Session = Depends(get_session),
):
    """
    Main feed endpoint.

    - Validates query params into PostFilterDTO
    - Builds a PostFilter (DB-layer filter object)
    - DB function list_posts_db() does all query logic (search, tags, rating)
    """
    f = PostFilter(
        q=filter_dto.q,
        tags=filter_dto.tags,
        match_all=filter_dto.match_all,
        min_rating=filter_dto.min_rating,
        max_rating=filter_dto.max_rating,
        limit=filter_dto.limit,
        offset=filter_dto.offset,
        order_by=filter_dto.order_by,
    )
    posts, total = list_posts_db(session, f)
    items = [post_to_dto(p) for p in posts]
    meta = PageMetaDTO(total=total, limit=f.limit, offset=f.offset)
    return PostPageDTO(items=items, meta=meta)


@app.get("/posts/{post_id}", response_model=PostReadDTO)
def get_post(post_id: int, session: Session = Depends(get_session)):
    post = get_post_db(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_dto(post)


# =============================================================================
# Routes: Tags
# =============================================================================


@app.get("/tags", response_model=list[TagReadDTO])
def list_tags(session: Session = Depends(get_session)):
    """
    Return all tags and how many posts use each tag.
    """
    tags_with_count = list_tags_db(session)
    return [TagReadDTO(id=t.id, name=t.name, count=t.count) for t in tags_with_count]


# =============================================================================
# Routes: Comments
# =============================================================================


@app.get("/posts/{post_id}/comments", response_model=list[CommentReadDTO])
def list_comments(post_id: int, session: Session = Depends(get_session)):
    post = get_post_db(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = list_comments_db(session, post_id)
    return [comment_to_dto(c) for c in comments]


@app.post(
    "/posts/{post_id}/comments",
    response_model=CommentReadDTO,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    post_id: int,
    payload: CommentCreateDTO,
    session: Session = Depends(get_session),
):
    post = get_post_db(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = add_comment_db(
        session,
        post_id=post_id,
        user=payload.user,
        text=payload.text,
    )
    return comment_to_dto(comment)


# =============================================================================
# Health
# =============================================================================


@app.get("/health")
def health():
    return {"ok": True}
