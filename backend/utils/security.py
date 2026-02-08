
import os
from cryptography.fernet import Fernet
import redis
from django.conf import settings

# Initialize Redis connection for key storage
redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)

def get_cipher_suite():
    key = settings.SECRET_KEY[:32].encode() # Use SECRET_KEY for simplicity in this demo, or a dedicated FERNET_KEY
    # Ensure 32 bytes for Fernet URL-safe base64-encoded key
    # In production, use os.environ.get('FERNET_KEY')
    # For now, generate a key or use a static one derived from SECRET_KEY if meaningful
    try:
        return Fernet(key) 
    except Exception:
        # Fallback for dev: generate a consistent key
        import base64
        # simple consistent key derivation
        k = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'='))
        return Fernet(k)

def encrypt_api_key(api_key: str) -> str:
    cipher_suite = get_cipher_suite()
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    cipher_suite = get_cipher_suite()
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

def store_api_keys(conversation_id: str, api_keys: dict, ttl: int = 3600):
    """
    Encrypts and stores API keys in Redis with a TTL.
    keys: {'openai': 'sk-...', 'gemini': '...', 'deepseek': '...'}
    """
    encrypted_data = {k: encrypt_api_key(v) for k, v in api_keys.items()}
    redis_client.hmset(f"api_keys:{conversation_id}", encrypted_data)
    redis_client.expire(f"api_keys:{conversation_id}", ttl)

def get_api_keys(conversation_id: str) -> dict:
    """
    Retrieves and decrypts API keys from Redis.
    """
    data = redis_client.hgetall(f"api_keys:{conversation_id}")
    if not data:
        return {}
    
    return {k.decode(): decrypt_api_key(v.decode()) for k, v in data.items()}
