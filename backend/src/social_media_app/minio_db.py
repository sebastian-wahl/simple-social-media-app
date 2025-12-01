from __future__ import annotations

import io
import uuid
import os

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from social_media_app.config import settings


def _get_minio_client() -> Minio:
    """
    Create a MinIO client based on values from settings.
    All MinIO configuration values originate from config.py, which
    in turn reads the global .env file.
    """
    endpoint = settings.MINIO_ENDPOINT  # e.g. "minio:9000"
    access_key = settings.MINIO_ROOT_USER or "minioadmin"
    secret_key = settings.MINIO_ROOT_PASSWORD or "minioadmin"
    secure = settings.MINIO_SECURE

    return Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    """
    Ensure that the bucket exists.
    Uses bucket_exists() when available; otherwise falls back to stat_object().
    Authentication or permission errors are raised immediately.
    """
    # Modern MinIO SDKs provide bucket_exists()
    bucket_exists = getattr(client, "bucket_exists", None)

    if callable(bucket_exists):
        try:
            if not client.bucket_exists(bucket):
                try:
                    client.make_bucket(bucket)
                except S3Error as exc:
                    code = (exc.code or "").lower()
                    if "bucketalreadyownedbyyou" in code or "bucketalreadyexists" in code:
                        return
                    raise
            return
        except S3Error as exc:
            code = (exc.code or "").lower()
            if "invalidaccesskeyid" in code or "accessdenied" in code:
                raise

    # Fallback: try stat_object
    try:
        client.stat_object(bucket, "__bucket_probe__")
        return
    except S3Error as exc:
        code = (exc.code or "").lower()

        if "nosuchbucket" in code or "resourcenotfound" in code:
            try:
                client.make_bucket(bucket)
                return
            except S3Error as make_exc:
                make_code = (make_exc.code or "").lower()
                if "bucketalreadyownedbyyou" in make_code or "bucketalreadyexists" in make_code:
                    return
                raise

        if "invalidaccesskeyid" in code or "accessdenied" in code:
            raise

        raise


def _guess_extension(content_type: str | None) -> str:
    """
    Infer a simple file extension based on the content type
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
    Upload an image file to MinIO and return the object key (image_path)
    - When MINIO_ENABLED=false, a dummy key is returned
    - When enabled, ensures the bucket exists and uploads the file
    """
    if not settings.MINIO_ENABLED:
        ext = _guess_extension(file.content_type)
        return f"dummy/{uuid.uuid4().hex}{ext}"

    client = _get_minio_client()
    bucket = os.getenv("MINIO_BUCKET") or settings.MINIO_BUCKET or "post-images"

    _ensure_bucket(client, bucket)

    ext = _guess_extension(file.content_type)
    key = f"posts/{uuid.uuid4().hex}{ext}"

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
    Check if an object exists in MinIO
    - When MINIO_ENABLED=false, always return True (dummy mode)
    """
    if not settings.MINIO_ENABLED:
        return True

    client = _get_minio_client()
    bucket = os.getenv("MINIO_BUCKET") or settings.MINIO_BUCKET or "post-images"

    try:
        client.stat_object(bucket, image_path)
        return True
    except S3Error as exc:
        code = (exc.code or "").lower()
        if "nosuchkey" in code or "nosuchbucket" in code or "resourcenotfound" in code:
            return False
        raise
