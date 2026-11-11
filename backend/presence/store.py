import time

import redis
from django.conf import settings


# Longest a token can live: its signing key's hour plus the following hour (presence.blind).
TOKEN_TTL_SECONDS = 7200
ACTIVE_WINDOW_SECONDS = 600
HEARTBEAT_MIN_INTERVAL_SECONDS = 30
TOKEN_ISSUE_HOURLY_LIMIT = 10
TOKEN_ISSUE_WINDOW_SECONDS = 3600
# Stored in place of a venue for a token that was rotated out, so it cannot be replayed.
RETIRED = "!retired"

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


def allow_issuance(user_id):
    key = f"presence:issued:{user_id}"
    pipe = client().pipeline()
    pipe.incr(key)
    pipe.expire(key, TOKEN_ISSUE_WINDOW_SECONDS, nx=True)
    count, _ = pipe.execute()
    return count <= TOKEN_ISSUE_HOURLY_LIMIT


def heartbeat(venue_id, token, previous=None):
    """Record that token is at venue_id now. The caller has already checked its signature.

    previous is the token this phone used before, if it just switched to a new one. Its
    presence is handed over so the phone is not counted twice, and it is retired so it
    cannot be replayed.
    """
    if previous == token:
        previous = None

    def update(pipe):
        last_venue = pipe.get(_token_key(token))
        if last_venue == RETIRED:
            return "invalid"
        now = time.time()
        if last_venue:
            last = pipe.zscore(_active_key(last_venue), token)
            if last is not None and now - last < HEARTBEAT_MIN_INTERVAL_SECONDS:
                return "throttled"
        previous_venue = pipe.get(_token_key(previous)) if previous is not None else None
        active = _active_key(venue_id)
        pipe.multi()
        if last_venue and last_venue != venue_id:
            pipe.zrem(_active_key(last_venue), token)
        if previous_venue is not None:
            if previous_venue != RETIRED:
                pipe.zrem(_active_key(previous_venue), previous)
            pipe.set(_token_key(previous), RETIRED, ex=TOKEN_TTL_SECONDS)
        pipe.zadd(active, {token: now})
        pipe.zremrangebyscore(active, 0, now - ACTIVE_WINDOW_SECONDS)
        pipe.expire(active, ACTIVE_WINDOW_SECONDS)
        pipe.set(_token_key(token), venue_id, ex=TOKEN_TTL_SECONDS)
        return "ok"

    # Watching both tokens makes a concurrent rotation retry instead of resurrecting one.
    keys = [_token_key(token)] + ([_token_key(previous)] if previous is not None else [])
    return client().transaction(update, *keys, value_from_callable=True)


def active_count(venue_id):
    cutoff = time.time() - ACTIVE_WINDOW_SECONDS
    return client().zcount(_active_key(venue_id), cutoff, "+inf")
