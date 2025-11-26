from __future__ import annotations

import io
import os
import uuid

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from social_media_app.config import settings


def _get_minio_client() -> Minio:
    """
    MinIO-Client aus Umgebungsvariablen erzeugen.
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
    Stelle sicher, dass der Bucket existiert.
    Ohne exists_bucket/bucket_exists zu benötigen (SDK-versionssicher).
    """
    # 1) Versuche stat_bucket (neuere SDKs)
    stat_bucket = getattr(client, "stat_bucket", None)
    if callable(stat_bucket):
        try:
            client.stat_bucket(bucket)
            return  # existiert
        except S3Error:
            # nicht vorhanden -> erstellen
            try:
                client.make_bucket(bucket)
                return
            except S3Error:
                # Wenn parallel bereits erstellt oder fehlende Rechte: weiter unten ggf. ignorieren
                pass

    # 2) Fallback: stat_object auf ein nicht-existierendes Objekt
    #    Wenn der Bucket fehlt, wirft MinIO i. d. R. ein 404/NoSuchBucket.
    try:
        client.stat_object(bucket, "__bucket_probe__")
        return  # Bucket existiert (Objekt ggf. nicht, aber Bucket schon)
    except S3Error as exc:
        err = getattr(exc, "code", "") or ""
        # Wenn der Fehler "NoSuchBucket" lautet, erstellen
        if "NoSuchBucket" in err or "ResourceNotFound" in err or exc.status == 404:
            try:
                client.make_bucket(bucket)
                return
            except S3Error:
                # Wenn es hier scheitert (z. B. bereits erstellt), ignorieren
                pass
        # andere Fehler ignorieren wir – Upload wird später ohnehin scheitern, falls der Bucket wirklich fehlt


def _guess_extension(content_type: str | None) -> str:
    """
    Rate einfache Dateiendung anhand des Content-Types.
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
    Bild hochladen und den Objekt-Key (image_path) zurückgeben.
    - Bei MINIO_ENABLED=false: Dummy-Schlüssel zurückgeben, kein MinIO-Zugriff.
    - Bei true: Bucket sicherstellen und Objekt hochladen.
    """
    # Dummy-Modus: niemals MinIO anfassen
    if  not settings.MINIO_ENABLED:
        ext = _guess_extension(file.content_type)
        return f"dummy/{uuid.uuid4().hex}{ext}"

    client = _get_minio_client()
    bucket = os.getenv("MINIO_BUCKET", "post-images")

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
    Prüfe, ob ein Objekt in MinIO existiert.
    - Bei MINIO_ENABLED=false immer True (damit der Flow im Dummy-Modus funktioniert).
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