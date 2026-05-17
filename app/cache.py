import redis
import json
import os

_client = None


def _get_redis():
    global _client
    if _client is not None:
        return _client
    try:
        url = os.getenv("REDIS_URL")
        if not url:
            return None
        _client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
        _client.ping()
        return _client
    except Exception:
        _client = None
        return None


def cache_get(key):
    r = _get_redis()
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key, data, ttl=300):
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(data, default=str))
    except Exception:
        pass


def cache_delete(key):
    r = _get_redis()
    if not r:
        return
    try:
        r.delete(key)
    except Exception:
        pass
