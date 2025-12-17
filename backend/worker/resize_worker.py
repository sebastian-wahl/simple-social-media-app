import os 
import io
import json
import pika
from minio import Minio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

#Configs
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "rabbitmq")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "minioadmin")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE_NAME", "image_resize_queue")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "post-images")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

THUMBNAIL_SIZE = (300, 300)

def get_minio_client():
    """CREATE MinIO client"""
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=MINIO_SECURE,
    )

def resize_image(image_path: str) -> str:
    """AAAAAAAAA"""
    print(f"[RESIZE] Processing: {image_path}")

    client = get_minio_client()

    try:
        response = client.get_object(MINIO_BUCKET, image_path)
        image_data = response.read()
        response.close()
        response.release_conn()
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None

    img = Image.open(io.BytesIO(image_data))

    img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

    thumb_buffer = io.BytesIO()
    img_format = img.format or 'JPEG'
    img.save(thumb_buffer, format=img_format, quality=85, optimize=True)
    thumb_buffer.seek{0}
    thumb_bytes = thumb_buffer.read()

    thumb_path = image_path.replace("posts/", "thumbs/", 1)

    try:
        client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=thumb_path,
            data=io.BytesIO(thumb_bytes),
            length=len(thumb_bytes),
            content_type=f"image/{img_format.lower()}",
        )
        print(f"Thumbnail created: {thumb_path}")
        return thumb_path
    except Exception as e:
        print("Failed to upload thumbnail: {e}")
        return None

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        image_path = message.get("image_path")
         
         if not image_path:
            print("No image_path in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        thumb_path = resize_image(image_path)

        if thumb_path:
            print("Thumbnail {thumb_path}")
        else:
            print("Could not create thumbnail for {image_path}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("Processing failed: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    print("Starting Image Resize Worker")
    print("Connecting to RabbitMQ at {RABBITMQ_HOST}....")

    credentials = pika.PlainCredentials(RABITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=credentials,
            heartbeat=600,
        )
    )

    channel = connection.channel()

    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    channel.basic_consume(
        queue=RABBITMQ_QUEUE,
        on_message_callback=callback,
    )

    print(f"Waiting for messages in queue: {RABBITMQ_QUEUE}")
    print("PRESS CTRL+C to exist")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n Shutting down...")
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()
    