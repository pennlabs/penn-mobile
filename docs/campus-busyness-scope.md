# Campus Busyness: Scope Split

Scope boundaries for the implementation described in [campus-busyness.md](./campus-busyness.md). This project implements everything up to and including heartbeat ingestion and the active presence store. Analytics and user-facing busyness data are owned by a separate project.

## In scope (this project)

Spec sections 1, 4–7, and the auth half of 13.

### Venue configuration (section 1)
- Venue model: `venue_id`, name, geofence, minimum dwell time, exit grace period, capacity, calibration info, minimum sample size, enabled flag
- Endpoint serving venue definitions to the app so location classification happens on-device

### Opt-in and anonymous identity (sections 5, 13)
- Opt-in status stored on the authenticated user, kept separate from presence reporting
- Issuance of short-lived rotating anonymous tokens that the app attaches to heartbeats
- Tokens must not be linkable to PennKey or reconstructable into long-term location history

### Presence ingestion API (sections 4, 6)
- Receives heartbeats: `venue_id`, token, timestamp. No GPS coordinates, no PennKey
- Validates the venue and the token
- Rejects duplicate or excessive updates (rate limiting)
- Stateless across backend instances

### Active presence store (section 7)
- Redis tracks active anonymous tokens per venue
- Heartbeats refresh presence; presence expires on TTL (~10 minutes) with no explicit exit event
- Handles token rotation without double-counting a device while its old token has not yet expired

## Out of scope (analytics project)

Spec sections 8–12. Built on top of the active presence store:

- Occupancy aggregation (unique active tokens per venue)
- Busyness categories (Not Busy / Moderate / Busy / Very Busy)
- Historical time buckets, baselines, percentiles, "busier than usual"
- Venue-level read API consumed by the app
- Frontend venue list and detail pages
- Minimum-count suppression ("Not enough data")

## Not in this repo

Spec sections 2–3 live in the iOS/Android apps:

- On-device location detection (raw GPS stays on the device)
- Presence state machine (Outside → Candidate → Present → Leaving)

The backend only ever sees heartbeats from devices already in the Present state.

## Handoff contract (implemented)

The analytics project reads Redis directly. If a heartbeat stream is needed instead, ingestion in `backend/presence/store.py` grows a publish step; raise it before building on polling.

- `presence:active:{venue_id}`: sorted set, member = anonymous token, score = Unix timestamp of last heartbeat. Active device count = members with score within the last `ACTIVE_WINDOW_SECONDS` (600). `presence.store.active_count(venue_id)` implements this.
- `presence:token:{token}`: validity marker, TTL `TOKEN_TTL_SECONDS` (3600). Value is the venue of the token's last heartbeat; used internally for rotation. Never map tokens to users.
- Guarantee: one live token = one participating device. Token rotation transfers sorted-set membership atomically, so a device is never counted twice during rotation.
- Heartbeats more frequent than `HEARTBEAT_MIN_INTERVAL_SECONDS` (30) are rejected with 429. Stale members are pruned on write; no janitor job exists.
- Token issuance is capped at `TOKEN_ISSUE_HOURLY_LIMIT` (10) per user per hour via a Redis counter, so one account cannot inflate device counts by minting tokens.

## API (implemented)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/presence/venues/` | user | Enabled venues with geofence and dwell config |
| GET/POST | `/presence/opt-in/` | user | Read or set `{"opted_in": bool}` |
| POST | `/presence/token/` | user + opt-in | Issue anonymous token; optional `previous` rotates |
| POST | `/presence/heartbeat/` | token only | `{venue_id, token}`; 204, or 400/403/429 |
