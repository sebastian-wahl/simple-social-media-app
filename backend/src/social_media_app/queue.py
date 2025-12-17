import json
import pika
from .config import settings

def get_rabbitmq_connection():
    """Create RabbitMQ connection"""
    if not settings.RABBITMQ_ENABLED:
        return None
    
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER,
        settings.RABBITMQ_PASSWORD
    )
    
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
    )
    
    return pika.BlockingConnection(parameters)

def publish_resize_task(image_path: str) -> bool:
    if not settings.RABBITMQ_ENABLED:
        print(" RabbitMQ is disabled, skipping resize task")
        return False
    
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare queue (idempotent)
        channel.queue_declare(queue=settings.RABBITMQ_QUEUE_NAME, durable=True)
        
        # Create message
        message = {
            "image_path": image_path,
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=settings.RABBITMQ_QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        
        print(f"Published resize task for: {image_path}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"Failed to publish resize task: {e}")
        return False
