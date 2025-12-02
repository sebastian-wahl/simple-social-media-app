from __future__ import annotations
import io
import pytest
from fastapi import UploadFile
from minio.error import S3Error
from starlette.datastructures import Headers
from social_media_app import minio_db
from social_media_app.config import settings
from social_media_app.minio_db import (
    _guess_extension,
    image_exists_in_minio,
    upload_image_to_minio,
)

# ---------------------------------------------------------------------------
# _guess_extension helper
# ---------------------------------------------------------------------------


def test_guess_extension_jpeg():
    assert _guess_extension("image/jpeg") == ".jpg"
    assert _guess_extension("image/jpg") == ".jpg"


def test_guess_extension_png_gif_and_fallback():
    assert _guess_extension("image/png") == ".png"
    assert _guess_extension("image/gif") == ".gif"
    assert _guess_extension("application/octet-stream") == ".bin"
    assert _guess_extension(None) == ".bin"


# ---------------------------------------------------------------------------
# upload_image_to_minio when MINIO is disabled
# ---------------------------------------------------------------------------


def test_upload_image_returns_dummy_key_when_disabled(monkeypatch):
    # Force MINIO_ENABLED=False
    monkeypatch.setattr(minio_db.settings, "MINIO_ENABLED", False)

    file = UploadFile(
        filename="test.jpg",
        file=io.BytesIO(b"fake-image-bytes"),
        headers=Headers({"content-type": "image/jpeg"}),
    )

    key = upload_image_to_minio(file)
    # Should be a dummy key that still looks like a file path
    assert key.startswith("dummy/")
    assert key.endswith(".jpg")


# ---------------------------------------------------------------------------
# image_exists_in_minio when MINIO is disabled
# ---------------------------------------------------------------------------


def test_image_exists_always_true_when_disabled(monkeypatch):
    monkeypatch.setattr(minio_db.settings, "MINIO_ENABLED", False)
    assert image_exists_in_minio("anything.jpg") is True


# ---------------------------------------------------------------------------
# upload_image_to_minio when MINIO is enabled, using a fake client
# ---------------------------------------------------------------------------


class FakeMinioClient:
    def __init__(self):
        self.bucket_exists_called_with = None
        self.make_bucket_called_with = None
        self.put_object_calls = []

    def bucket_exists(self, bucket: str) -> bool:
        self.bucket_exists_called_with = bucket
        # pretend bucket does not exist so _ensure_bucket creates it
        return False

    def make_bucket(self, bucket: str) -> None:
        self.make_bucket_called_with = bucket

    def put_object(self, bucket_name, object_name, data, length, content_type):
        self.put_object_calls.append(
            {
                "bucket_name": bucket_name,
                "object_name": object_name,
                "length": length,
                "content_type": content_type,
            }
        )


def test_upload_image_uses_fake_minio_client(monkeypatch):
    monkeypatch.setattr(minio_db.settings, "MINIO_ENABLED", True)

    fake_client = FakeMinioClient()
    monkeypatch.setattr(minio_db, "_get_minio_client", lambda: fake_client)
    monkeypatch.setenv("MINIO_BUCKET", "test-bucket")

    file_bytes = b"hello"
    file = UploadFile(
        filename="test.png",
        file=io.BytesIO(file_bytes),
        headers=Headers({"content-type": "image/png"}),
    )

    key = upload_image_to_minio(file)

    # Should generate a posts/<uuid>.png key
    assert key.startswith("posts/")
    assert key.endswith(".png")

    # Bucket should have been ensured
    assert fake_client.bucket_exists_called_with == "test-bucket"
    assert fake_client.make_bucket_called_with == "test-bucket"

    # put_object should have been called once with our bucket and key
    assert len(fake_client.put_object_calls) == 1
    call = fake_client.put_object_calls[0]
    assert call["bucket_name"] == "test-bucket"
    assert call["object_name"] == key
    assert call["length"] == len(file_bytes)
    assert call["content_type"] == "image/png"


# ---------------------------------------------------------------------------
# image_exists_in_minio when enabled, with fake client
# ---------------------------------------------------------------------------


class FakeMinioClientForStat:
    def __init__(self, exists: bool):
        self.exists = exists
        self.stat_calls = []

    def stat_object(self, bucket, image_path):
        self.stat_calls.append((bucket, image_path))
        if not self.exists:
            # Raise a real S3Error so image_exists_in_minio catches it
            raise S3Error(
                code="NoSuchKey",
                message="Object does not exist",
                resource=image_path,
                request_id="req",
                host_id="host",
                response=None,  # extra parameter required by this version
            )


def test_image_exists_true_if_stat_succeeds(monkeypatch):
    monkeypatch.setattr(minio_db.settings, "MINIO_ENABLED", True)
    fake_client = FakeMinioClientForStat(exists=True)
    monkeypatch.setattr(minio_db, "_get_minio_client", lambda: fake_client)
    monkeypatch.setenv("MINIO_BUCKET", "test-bucket")

    assert image_exists_in_minio("posts/exists.jpg") is True
    assert fake_client.stat_calls == [("test-bucket", "posts/exists.jpg")]


def test_image_exists_false_if_stat_raises(monkeypatch):
    monkeypatch.setattr(minio_db.settings, "MINIO_ENABLED", True)
    fake_client = FakeMinioClientForStat(exists=False)
    monkeypatch.setattr(minio_db, "_get_minio_client", lambda: fake_client)
    monkeypatch.setenv("MINIO_BUCKET", "test-bucket")

    assert image_exists_in_minio("posts/missing.jpg") is False
    assert fake_client.stat_calls == [("test-bucket", "posts/missing.jpg")]