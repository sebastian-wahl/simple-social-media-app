import io
from PIL import Image

from src.worker.resize_worker import resize_image


class FakeMinioClient:
    def __init__(self):
        self.objects = {}

    def get_object(self, bucket, path):
        img = Image.new("RGB", (800, 600))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        class Obj:
            def read(self): return buf.read()
            def close(self): pass
            def release_conn(self): pass

        return Obj()

    def put_object(self, bucket_name, object_name, data, length, content_type):
        self.objects[object_name] = data.read()


def test_resize_image_creates_thumbnail(monkeypatch):
    fake_client = FakeMinioClient()

    monkeypatch.setattr(
        "src.worker.resize_worker.get_minio_client",
        lambda: fake_client,
    )

    thumb_path = resize_image("posts/test.jpg")

    assert thumb_path == "thumbs/test.jpg"
    assert "thumbs/test.jpg" in fake_client.objects
