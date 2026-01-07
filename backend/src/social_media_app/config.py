import os

from dotenv import load_dotenv

# Loads environment variables from .env automatically
load_dotenv()


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///app.db")

    MINIO_ENABLED = os.getenv("MINIO_ENABLED", "true").lower() == "true"
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "post-images")

    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "true").lower() == "true"
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "rabbitmq")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "rabbitmq")
    RABBITMQ_RESIZE_QUEUE: str = os.getenv("RABBITMQ_RESIZE_QUEUE", "image_resize_queue")
    RABBITMQ_SENTIMENT_QUEUE: str = os.getenv("RABBITMQ_SENTIMENT_QUEUE","sentiment_queue")


settings = Settings()
