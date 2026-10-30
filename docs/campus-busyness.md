# Penn Mobile Campus Busyness

## Goal

Build a Penn Mobile feature that lets opted-in users see how busy important campus locations are, such as Pottruck and dining halls.

For each venue, users should be able to see:

- Current busyness category
- Number of active participating devices
- Whether it is busier or quieter than usual
- Historical trends by time of day and day of week
- Confidence / whether enough data exists

Users who are not opted in should not be able to view the data and should instead see an opt-in screen with clear privacy information.

---

## High-Level Architecture

```text
Venue Configuration
        ↓
On-Device Location Detection
        ↓
Presence State Machine
        ↓
Anonymous Presence Heartbeats
        ↓
Presence Ingestion API
        ↓
Active Presence Store
        ↓
Occupancy Aggregation
        ↓
Busyness Model + Historical Baselines
        ↓
Penn Mobile API
        ↓
Busyness UI
```

## 1. Venue Configuration

Define the locations supported by the system.

Each venue can include:

- `venue_id`
- Name
- Geofence
- Minimum dwell time
- Exit grace period
- Capacity
- Calibration information
- Minimum sample size
- Enabled/disabled status

Venue definitions are sent to Penn Mobile so location classification can happen locally.

## 2. On-Device Detection

Penn Mobile uses device location signals to determine whether the user may be inside a supported venue.

Raw latitude and longitude should stay on the device.

The client only determines a candidate `venue_id`.

## 3. Presence State Machine

Each venue can have the following local states:

```text
Outside → Candidate → Present → Leaving → Outside
```

- **Outside:** not at the venue
- **Candidate:** detected inside, but not long enough yet
- **Present:** remained inside for the required dwell time
- **Leaving:** appears to have left, but waits briefly to avoid GPS noise

Example:

```text
Enter Pottruck
→ Candidate

Remain inside for 3 minutes
→ Present

Leave geofence
→ Leaving

Remain outside
→ Outside
```

## 4. Presence Reporting

The device only sends data while it is in the `Present` state.

```text
Outside   → send nothing
Candidate → send nothing
Present   → send periodic heartbeat
Leaving   → stop heartbeats
```

Example heartbeat:

```json
{
  "venue_id": "pottruck",
  "token": "temporary_anonymous_token",
  "timestamp": "..."
}
```

No raw GPS coordinates or PennKey should be included.

## 5. Privacy / Anonymous Identity

Presence reports should use short-lived rotating tokens instead of permanent anonymous IDs.

Goals:

- Raw GPS never leaves the device
- No PennKey is sent with presence
- Tokens cannot easily be used to reconstruct long-term location history
- Individual presence data is temporary
- Historical storage contains aggregates, not user trajectories

Implementation note: authenticated token issuance and rotation can be correlated by the
server. The current implementation stores no token-to-account mapping, but it does not
provide cryptographic unlinkability. See [the scope and API contract](./campus-busyness-scope.md)
for the current consent contract, token lifetime, opt-out behavior, and remaining limits.

## 6. Presence Ingestion API

The backend receives heartbeats and:

- Validates the venue
- Validates the request/token
- Prevents duplicate or excessive updates
- Updates the device's temporary presence
- Remains stateless across backend instances

## 7. Active Presence Store

Use something like Redis to track active anonymous tokens by venue.

Heartbeats refresh presence.

If heartbeats stop, presence automatically expires after a timeout, such as 10 minutes.

This avoids requiring explicit exit events and handles app crashes, dead phones, lost connectivity, etc.

## 8. Occupancy Aggregation

For each venue, count the number of unique active tokens.

Example:

```text
Pottruck → 73 active participating devices
```

Only aggregated counts should be stored long term.

## 9. Busyness Model

Convert active-device counts into useful user-facing information.

Initial outputs could include:

- Not Busy
- Moderate
- Busy
- Very Busy

The system should also compare the current count against historical behavior for the same:

- Venue
- Day of week
- Time of day

Example:

```text
Pottruck
BUSY
73 participating devices
24% busier than usual for Friday at 5 PM
```

Initially, it may be better to show relative busyness rather than estimating the exact number of people.

## 10. Historical Trends

Store aggregate counts in time buckets, for example every 5 minutes.

This allows the system to calculate:

- Typical busyness by time of day
- Typical busyness by day of week
- Historical percentiles
- "Busier than usual" comparisons
- Google Maps-style trend charts

No individual identifiers should be stored in historical data.

## 11. Penn Mobile API

Expose venue-level data to the app.

Example:

```json
{
  "venue_id": "pottruck",
  "active_devices": 73,
  "busyness": "BUSY",
  "relative_to_usual": 1.24,
  "confidence": "HIGH",
  "updated_at": "...",
  "historical_trend": []
}
```

The frontend should not need to know how location collection works.

## 12. Frontend

Possible venue list:

```text
Pottruck           VERY BUSY
                   ↑ Busier than usual

1920 Commons       MODERATE
                   Typical right now

Houston Hall       NOT BUSY
                   ↓ Quieter than usual
```

Each venue could have a detail page with:

- Current status
- Active device count
- Comparison to normal
- Historical graph
- Last updated time

A campus heatmap could be added later.

## 13. Opt-In

Only users who contribute presence data should be able to view busyness information.

Users who are not opted in should see:

- Feature explanation
- Clear privacy guarantees
- Opt-in button

Authentication/opt-in status should remain separate from anonymous presence reporting.

## 14. Important Open Problems

### Calibration

The number of participating Penn Mobile devices will not equal actual occupancy.

The system needs to understand how well device counts correlate with true busyness.

Calibration may need to differ by venue.

### Low Adoption

If very few people opt in, the data may not be useful.

Possible incentives include making busyness information available only to participating users.

### Privacy

Small counts should probably not be displayed.

Example:

```text
active devices < minimum threshold
→ "Not enough data"
```

### Background Location

Reliable low-power background detection on iOS/Android will need experimentation.

Continuous GPS polling should be avoided if possible.

### Abuse Prevention

Because presence reports are anonymous, the backend must prevent fake devices from submitting thousands of reports.

Possible tools include:

- Rate limiting
- Short-lived signed credentials
- App Attest / DeviceCheck
- Anonymous authorization mechanisms

## MVP

A reasonable first version:

1. Support a small number of venues
2. Detect venue presence locally
3. Use `Outside → Candidate → Present`
4. Send anonymous heartbeats only while Present
5. Track active tokens in Redis
6. Aggregate active-device counts
7. Store historical aggregate counts
8. Compare current counts against historical baselines
9. Return `Not Busy / Moderate / Busy / Very Busy`
10. Show venue list + historical trend graph in Penn Mobile

The main technical questions to validate first are whether background location works reliably and whether participating-device counts are sufficiently correlated with actual venue busyness.
