
import json
import redis
from django.conf import settings

# Redis client for pub/sub
redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)

def publish_update(conversation_id: str, data: dict):
    """
    Publishes an update to the conversation channel.
    channel: conversation_{id}
    data: dict to be JSON serialized
    """
    channel = f"conversation_{conversation_id}"
    redis_client.publish(channel, json.dumps(data))

def publish_chunk(conversation_id: str, agent_name: str, token: str, round_num: int):
    """
    Publishes a single token/chunk to the frontend for streaming.
    """
    publish_update(conversation_id, {
        "type": "token",
        "agent": agent_name,
        "content": token,
        "round": round_num
    })
