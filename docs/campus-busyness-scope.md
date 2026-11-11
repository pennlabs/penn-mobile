# Campus Busyness: Scope Split

Scope boundaries for the implementation described in [campus-busyness.md](./campus-busyness.md). This project implements everything up to and including heartbeat ingestion and the active presence store. Analytics and user-facing busyness data are owned by a separate project.

## In scope (this project)

Spec sections 1, 4–7, and the auth half of 13.

### Venue configuration (section 1)
- Venue model: `venue_id`, name, geofence, minimum dwell time, capacity, calibration info, minimum sample size, enabled flag
- Endpoint serving venue definitions to the app so location classification happens on-device

### Opt-in and anonymous identity (sections 5, 13)
- Opt-in status stored on the authenticated user, kept separate from presence reporting
- Short-lived anonymous tokens that the app makes itself and attaches to heartbeats
- The server blind-signs each token (RFC 9474, `RSABSSA-SHA384-PSS-Deterministic`) for an
  opted-in account without seeing it, so a heartbeat cannot be matched to the account that
  requested the signature. No visit history is stored. IP address and timing are not hidden.

### Presence ingestion API (sections 4, 6)
- Receives heartbeats: `venue_id`, token, timestamp. No GPS coordinates, no PennKey
- Validates the venue and the token's signature
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
- `presence:token:{token}`: the venue of the token's last heartbeat, TTL `TOKEN_TTL_SECONDS` (7200). Created on the first heartbeat, not at issuance. A rotated-out token holds `!retired` so it cannot be replayed. Never map tokens to users.
- `presence:signing-key:{hour}`: that hour's RSA private key, encrypted with `SECRET_KEY`, shared by all web workers. A key signs for one hour and is accepted on heartbeats for that hour and the next, so a token lives one to two hours.
- A heartbeat with `previous_token` transfers sorted-set membership atomically and retires the
  old token. Moving venues removes the token's previous membership. The client must use one
  token per device; token issuance alone does not enforce a one-device guarantee.
- Heartbeats more frequent than `HEARTBEAT_MIN_INTERVAL_SECONDS` (30) are rejected with 429. Stale members are pruned on write; no janitor job exists.
- Token issuance is capped at `TOKEN_ISSUE_HOURLY_LIMIT` (10) per user per hour via a Redis
  counter. This bounds issuance but does not prevent multiple fresh tokens from one account.

## API (implemented)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/presence/venues/` | user | Enabled venues with geofence and dwell config |
| GET/POST | `/presence/opt-in/` | user | Read consent/privacy; enable with `{"opted_in": true, "policy_version": "presence-v1"}`; disable with `{"opted_in": false}` |
| GET | `/presence/token-key/` | none | Current public signing key: `{key_id, algorithm, public_key, issues_for, token_expires_in}` |
| POST | `/presence/token/` | user + opt-in | Blind-sign a token: `{key_id, blinded_message}` returns `{key_id, blind_signature, expires_in}`; 409 with the new key if the key rotated |
| POST | `/presence/heartbeat/` | signed token only | `{venue_id, token, key_id, signature}`, optional `previous_token`; 204, or 400/403/429 |

`/api/presence/` is the canonical prefix; root aliases also work. Heartbeat `timestamp`
is optional and ignored: sorted-set scores use server receive time. Opt-out stops issuance;
the app must stop sending, and previously signed tokens remain valid until expiry.

Client token flow: fetch the key, make a random token (32 random bytes, base64url), blind it,
POST the blinded message, unblind the reply into a signature, then send token, `key_id` and
signature on every heartbeat. Binary fields are base64. To switch tokens, send the old one
as `previous_token` on the new token's first heartbeat. `backend/tests/presence/blind_client.py`
is a short reference implementation of the client side.

Use the existing `Venue` and `PresenceOptIn` models; there is no parallel location/consent
registry. Venue IDs are stable strings across gym, dining, and library locations; dining
IDs remain separate source references. Geofences use `lat`, `lng`, and `radius_m`.
Run `python manage.py import_tracked_locations [file] [--dry-run]` after loading dining and
fitness sources to import the disabled pilot definitions.
