import json
import logging
import os
from typing import Tuple

import pika
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select
from transformers import pipeline

from social_media_app.models import Comment, Post
from sqlmodel import select

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentiment-worker")

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "rabbitmq")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_SENTIMENT_QUEUE", "sentiment_queue")

# -----------------------------------------------------------------------------
# Model (loaded ONCE)
# -----------------------------------------------------------------------------
logger.info("Loading sentiment model...")
classifier = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=-1,  # FORCE CPU
)
logger.info("Sentiment model loaded")

# -----------------------------------------------------------------------------
# DB
# -----------------------------------------------------------------------------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Run sentiment analysis on a text.
    Returns: (label, score)
    """
    result = classifier(text)[0]
    return result["label"], float(result["score"])


def update_comment_sentiment(
    session: Session,
    *,
    comment_id: int,
    sentiment: str,
    score: float,
) -> int | None:
    comment = session.exec(
        select(Comment).where(Comment.id == comment_id)
    ).first()

    if not comment:
        logger.warning("Comment %s not found, skipping", comment_id)
        return None

    comment.sentiment = sentiment
    comment.sentiment_score = score
    session.add(comment)
    session.commit()

    return comment.post_id

SENTIMENT_MAP = {
    "negative": -1.0,
    "neutral": 0.0,
    "positive": 1.0,
}

def recompute_post_rating(session: Session, post_id: int) -> None:
    comments = session.exec(
        select(Comment).where(Comment.post_id == post_id)
    ).all()

    if not comments:
        rating = 0.0
    else:
        values = [
            SENTIMENT_MAP[c.sentiment] * c.sentiment_score
            for c in comments
            if c.sentiment in SENTIMENT_MAP and c.sentiment_score is not None
        ]

        if not values:
            rating = 0.0
        else:
            avg = sum(values) / len(values)
            rating = ((avg + 1) / 2) * 4 + 1
            rating = max(1.0, min(5.0, rating))

    post = session.get(Post, post_id)
    if post:
        post.rating = round(rating, 2)
        session.add(post)
        session.commit()


# -----------------------------------------------------------------------------
# RabbitMQ callback
# -----------------------------------------------------------------------------
def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        comment_id = message.get("comment_id")
        text = message.get("text")

        if not comment_id or not text:
            logger.warning("Invalid message: %s", message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        sentiment, score = analyze_sentiment(text)

        with Session(engine) as session:
            post_id = update_comment_sentiment(
                session,
                comment_id=comment_id,
                sentiment=sentiment,
                score=score,
            )
        
            if post_id is not None:
                recompute_post_rating(session, post_id)

        logger.info(
            "Updated comment %s → %s (%.3f)",
            comment_id,
            sentiment,
            score,
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        logger.exception("Processing failed: %s", exc)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------
def main():
    logger.info("Starting Sentiment Worker")

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
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

    logger.info("Waiting for messages on queue: %s", RABBITMQ_QUEUE)
    channel.start_consuming()


if __name__ == "__main__":
    main()
