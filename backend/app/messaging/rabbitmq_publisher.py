# messaging/publisher.py
import json
import logging
import pika
from datetime import datetime, timezone
from app.messaging.rabbitmq_connection import get_rabbitmq_connection
from app.messaging.events import ML_EVENTS_QUEUE

logger = logging.getLogger(__name__)


def publish_event(event_type: str, payload: dict) -> None:
    message = {
        "event":     event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    connection = get_rabbitmq_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=ML_EVENTS_QUEUE, durable=True)

        channel.basic_publish(
            exchange="",
            routing_key=ML_EVENTS_QUEUE,
            body=json.dumps(message, default=str),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        logger.info(f"[RabbitMQ] Published | event={event_type}")

    except Exception as e:
        logger.error(f"[RabbitMQ] Publish failed | event={event_type} | error={e}")
        raise

    finally:
        connection.close()
        
    