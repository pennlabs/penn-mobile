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
    token = secrets.token_urlsafe(32)

    def rotate(pipe):
        venue_id = pipe.get(_token_key(previous)) if previous is not None else None
        if previous is not None and venue_id is None:
            return None
        score = pipe.zscore(_active_key(venue_id), previous) if venue_id else None
        pipe.multi()
        pipe.set(_token_key(token), venue_id or "", ex=TOKEN_TTL_SECONDS)
        if score is not None:
            pipe.zadd(_active_key(venue_id), {token: score})
            pipe.zrem(_active_key(venue_id), previous)
        if previous is not None:
            pipe.delete(_token_key(previous))
        return token

    keys = (_token_key(previous),) if previous is not None else ()
    return client().transaction(rotate, *keys, value_from_callable=True)


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
    def update(pipe):
        previous_venue = pipe.get(_token_key(token))
        if previous_venue is None:
            return "invalid"
        now = time.time()
        previous_active = _active_key(previous_venue) if previous_venue else _active_key(venue_id)
        last = pipe.zscore(previous_active, token)
        if last is not None and now - last < HEARTBEAT_MIN_INTERVAL_SECONDS:
            return "throttled"
        active = _active_key(venue_id)
        pipe.multi()
        if previous_venue and previous_venue != venue_id:
            pipe.zrem(previous_active, token)
        pipe.zadd(active, {token: now})
        pipe.zremrangebyscore(active, 0, now - ACTIVE_WINDOW_SECONDS)
        pipe.expire(active, ACTIVE_WINDOW_SECONDS)
        pipe.set(_token_key(token), venue_id, keepttl=True)
        return "ok"

    # Watching the token prevents concurrent rotation/expiry from resurrecting it.
    return client().transaction(update, _token_key(token), value_from_callable=True)


def active_count(venue_id):
    cutoff = time.time() - ACTIVE_WINDOW_SECONDS
    return client().zcount(_active_key(venue_id), cutoff, "+inf")
