import secrets
import time

import redis
from django.conf import settings


TOKEN_TTL_SECONDS = 3600
ACTIVE_WINDOW_SECONDS = 600
HEARTBEAT_MIN_INTERVAL_SECONDS = 30
TOKEN_ISSUE_HOURLY_LIMIT = 10

_client = None


def client():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def _token_key(token):
    return f"presence:token:{token}"


def _active_key(venue_id):
    return f"presence:active:{venue_id}"


def issue_token(previous=None):
    r = client()
    token = secrets.token_urlsafe(32)
    r.set(_token_key(token), "", ex=TOKEN_TTL_SECONDS)
    if previous is not None:
        venue_id = r.get(_token_key(previous))
        if venue_id:
            score = r.zscore(_active_key(venue_id), previous)
            if score is not None:
                r.zadd(_active_key(venue_id), {token: score})
                r.zrem(_active_key(venue_id), previous)
            r.set(_token_key(token), venue_id, keepttl=True)
        r.delete(_token_key(previous))
    return token


def is_valid_token(token):
    return client().exists(_token_key(token)) == 1


def allow_issuance(user_id):
    key = f"presence:issued:{user_id}"
    pipe = client().pipeline()
    pipe.incr(key)
    pipe.expire(key, TOKEN_TTL_SECONDS, nx=True)
    count, _ = pipe.execute()
    return count <= TOKEN_ISSUE_HOURLY_LIMIT


def heartbeat(venue_id, token):
    r = client()
    if not is_valid_token(token):
        return "invalid"
    now = time.time()
    active = _active_key(venue_id)
    last = r.zscore(active, token)
    if last is not None and now - last < HEARTBEAT_MIN_INTERVAL_SECONDS:
        return "throttled"
    pipe = r.pipeline()
    pipe.zadd(active, {token: now})
    pipe.zremrangebyscore(active, 0, now - ACTIVE_WINDOW_SECONDS)
    pipe.expire(active, ACTIVE_WINDOW_SECONDS)
    pipe.set(_token_key(token), venue_id, keepttl=True)
    pipe.execute()
    return "ok"


def active_count(venue_id):
    cutoff = time.time() - ACTIVE_WINDOW_SECONDS
    return client().zcount(_active_key(venue_id), cutoff, "+inf")
