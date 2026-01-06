"""RabbitMQ Queue Service for async tasks."""

import json
import logging
from typing import Any

import pika
from pika.exceptions import AMQPConnectionError

from social_media_app.config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for publishing messages to RabbitMQ."""

    def __init__(self) -> None:
        """Initialize RabbitMQ connection."""
        self.host = settings.RABBITMQ_HOST
        self.port = settings.RABBITMQ_PORT
        self.user = settings.RABBITMQ_USER
        self.password = settings.RABBITMQ_PASSWORD
        self.connection = None
        self.channel = None

    def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ at %s:%s", self.host, self.port)
        except AMQPConnectionError as e:
            logger.exception("Failed to connect to RabbitMQ: %s", e)
            raise

    def declare_queue(self, queue_name: str) -> None:
        """Declare a queue in RabbitMQ."""
        if not self.channel:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)
        logger.info("Queue '%s' declared", queue_name)

    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        """Publish a message to a queue."""
        if not self.channel:
            self.connect()

        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            ),
        )
        logger.info("Published message to queue '%s': %s", queue_name, message)

    def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Global instance
queue_service = QueueService()
