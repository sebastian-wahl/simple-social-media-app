from __future__ import annotations

import io
import os
import uuid

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from social_media_app.config import settings


# ToDo configure correctly once docker is finished
def _get_minio_client() -> Minio:
    """
    Create a MinIO client using environment variables.

    Expected env vars:
      - MINIO_ENDPOINT
      - MINIO_ACCESS_KEY
      - MINIO_SECRET_KEY
      - MINIO_SECURE
      - MINIO_BUCKET
    """
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    return Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    """
    Make sure the target bucket exists.
    Dev-friendly: create bucket automatically if missing.
    """
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def _guess_extension(content_type: str | None) -> str:
    """
    Guess a simple file extension from content type.
    """
    if not content_type:
        return ".bin"

    ct = content_type.lower()

    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "png" in ct:
        return ".png"
    if "gif" in ct:
        return ".gif"

    return ".bin"


def upload_image_to_minio(file: UploadFile) -> str:
    """
    Upload a single image file to MinIO and return the object key (image_path).

    Flow:
      1. Create MinIO client.
      2. Ensure bucket exists.
      3. Generate object key: "posts/<uuid>.ext".
      4. Read file bytes.
      5. Upload to MinIO.
      6. Return key for DB storage.

    NOTE:
      This reads the whole file into memory.
      For large files, switch to streaming upload.
    """

    # If MINIO_ENABLED=false, just return a fake key so the rest of the flow works.
    if not settings.MINIO_ENABLED:
        ext = _guess_extension(file.content_type)
        return f"dummy/{uuid.uuid4().hex}{ext}"
    client = _get_minio_client()
    bucket = os.getenv("MINIO_BUCKET", "post-images")

    _ensure_bucket(client, bucket)

    ext = _guess_extension(file.content_type)
    key = f"posts/{uuid.uuid4().hex}{ext}"

    # Read all bytes (simple approach)
    data_bytes = file.file.read()
    data_stream = io.BytesIO(data_bytes)

    try:
        client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=data_stream,
            length=len(data_bytes),
            content_type=file.content_type or "application/octet-stream",
        )
    except S3Error as exc:
        raise RuntimeError(f"Failed to upload image to MinIO: {exc}") from exc

    return key


def image_exists_in_minio(image_path: str) -> bool:
    """
    Check whether an object exists in MinIO.

    Returns:
        True if the object exists, otherwise False.
    """

    if not settings.MINIO_ENABLED:
        return True

    client = _get_minio_client()
    bucket = os.getenv("MINIO_BUCKET", "post-images")
    try:
        client.stat_object(bucket, image_path)
        return True
    except S3Error:
        return False
