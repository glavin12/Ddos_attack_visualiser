# Global DDoS Radar --- Final Implementation Plan

> **Status: FROZEN IMPLEMENTATION SPEC**
>
> This document is the implementation contract for the Global DDoS Radar
> project. Do not redesign the architecture while implementing
> individual features unless a real Cloudflare response contradicts this
> document. If a response contradicts an assumption, stop at the adapter
> boundary, record the discrepancy, and update the contract before
> changing downstream code.

------------------------------------------------------------------------

# 1. Project Definition

## 1.1 What we are building

Global DDoS Radar is an interactive cybersecurity visualization and
analytics website powered by Cloudflare Radar aggregate telemetry.

The project has two distinct data layers:

1.  **Real aggregate data**
    -   Cloudflare Radar provides country-to-country attack shares,
        country distributions, attack characteristics, and historical
        relative activity.
2.  **Synthetic visualization**
    -   The backend converts those aggregate distributions into
        temporary visual events for the globe.

The synthetic events are **not individual observed attacks**.

The project is statistically grounded, spatially synthetic.

## 1.2 Core principle

> Cloudflare determines the statistical distribution. The synthetic
> engine determines the visual realization.

Cloudflare data determines:

-   attack-pair relationships
-   relative attack shares
-   origin distributions
-   target distributions
-   protocol/vector/HTTP-method distributions
-   historical relative activity

Our system generates:

-   synthetic geographic points
-   event timing
-   active event count
-   particle movement
-   visual intensity
-   temporary visualization events

## 1.3 What we are NOT building

Do not turn this project into:

-   a DDoS attack tool
-   a packet generator
-   a botnet
-   an individual IP attribution system
-   an individual attack recorder
-   a claim that a particular real packet came from a particular
    coordinate
-   a fake "live individual attack feed"

The project visualizes aggregate telemetry.

------------------------------------------------------------------------

# 2. Final Product Structure

The website has three major experiences.

``` text
GLOBAL DDOS RADAR
│
├── 1. GLOBAL RADAR
│      └── Interactive 3D globe
│
├── 2. ATTACK ANALYTICS
│      ├── Top origins
│      ├── Top targets
│      └── Attack characteristics
│
└── 3. HISTORY
       └── Seven-day L3/L7 activity chart
```

## 2.1 Global Radar

The globe is the visual centerpiece.

It displays:

-   source/target attack arcs
-   moving particles
-   small synthetic geographic activity points
-   destination impact/pulse effects
-   multiple simultaneous routes
-   route density based on Radar shares
-   controlled active-event count

The globe must remain visually readable.

Do not render hundreds of simultaneous points merely because a share is
large.

## 2.2 Attack Analytics

Show the actual normalized Radar distributions.

Sections:

-   top attack origins
-   top attack targets
-   Layer 3 protocol distribution
-   Layer 3 attack vector distribution
-   Layer 7 HTTP method distribution

## 2.3 History

Show the seven-day historical time series.

Supported views:

-   Layer 3
-   Layer 7

The timeseries values are relative `MIN0_MAX` values.

They must not be presented as:

-   Mbps
-   packets per second
-   absolute bytes
-   absolute request counts

------------------------------------------------------------------------

# 3. Cloudflare Data Sources

The current implementation uses 11 Radar endpoints.

## 3.1 Attack pairs

### Layer 3

``` text
/attacks/layer3/top/attacks?limit=100&dateRange=1d
```

Purpose:

-   source-to-target relationships
-   globe arcs
-   route sampling

Units:

``` text
bytes
```

Normalization:

``` text
PERCENTAGE
```

### Layer 7

``` text
/attacks/layer7/top/attacks?limit=100&dateRange=1d
```

Purpose:

-   source-to-target relationships
-   globe arcs
-   route sampling

Units:

``` text
requests
```

Normalization:

``` text
PERCENTAGE
```

The Layer 3 sample does not contain `rank`. The Layer 7 sample does
contain `rank`.

Therefore `rank` is optional in the normalized attack-pair model.

------------------------------------------------------------------------

# 4. Country Distributions

## 4.1 Layer 3 origin

``` text
/attacks/layer3/top/locations/origin?limit=50&dateRange=1d
```

Purpose:

-   top-origin ranking
-   country-level analytics

Units:

``` text
bytes
```

## 4.2 Layer 3 target

``` text
/attacks/layer3/top/locations/target?limit=50&dateRange=1d
```

Purpose:

-   top-target ranking
-   country-level analytics

Units:

``` text
bytes
```

## 4.3 Layer 7 origin

``` text
/attacks/layer7/top/locations/origin?limit=50&dateRange=1d
```

Purpose:

-   top-origin ranking
-   country-level analytics

Units:

``` text
requests
```

## 4.4 Layer 7 target

``` text
/attacks/layer7/top/locations/target?limit=50&dateRange=1d
```

Purpose:

-   top-target ranking
-   country-level analytics

Units:

``` text
requests
```

## Critical rule

Origin-only and target-only distributions **must not** be used to
reconstruct source-to-target attack pairs.

The pair endpoint is the source of source-to-target relationships.

------------------------------------------------------------------------

# 5. Attack Characteristics

## 5.1 Layer 3 protocol

``` text
/attacks/layer3/summary/protocol?dateRange=1d
```

Purpose:

-   protocol distribution chart

Examples:

``` text
UDP
TCP
GRE
ICMP
```

Units:

``` text
bytes
```

## 5.2 Layer 3 vector

``` text
/attacks/layer3/summary/vector?dateRange=1d
```

Purpose:

-   attack-vector distribution

Examples from the sample:

``` text
Mirai (UDP) Flood
SYN Flood
UDP Flood
DNS Flood
SFU Flood
DNS Amplification
ACK Flood
Mirai (TCP) Flood
QUIC Flood
other
```

Units:

``` text
bytes
```

## 5.3 Layer 7 HTTP method

``` text
/attacks/layer7/summary/http_method?dateRange=1d
```

Purpose:

-   HTTP method distribution

Examples:

``` text
GET
POST
HEAD
OPTIONS
PATCH
PUT
DELETE
UNKNOWN
ACL
other
```

Units:

``` text
requests
```

------------------------------------------------------------------------

# 6. Historical Data

## 6.1 Layer 3 history

``` text
/attacks/layer3/timeseries?dateRange=7d&aggInterval=1h
```

Units:

``` text
bytes
```

Normalization:

``` text
MIN0_MAX
```

Aggregation:

``` text
ONE_HOUR
```

## 6.2 Layer 7 history

``` text
/attacks/layer7/timeseries?dateRange=7d&aggInterval=1h
```

Units:

``` text
requests
```

Normalization:

``` text
MIN0_MAX
```

Aggregation:

``` text
ONE_HOUR
```

The sample contains 167 hourly points.

------------------------------------------------------------------------

# 7. Data Collection Strategy

## 7.1 Current source-window decision

The current top, location, and summary requests use:

``` text
dateRange=1d
```

Historical requests use:

``` text
dateRange=7d
aggInterval=1h
```

The visualization is therefore based on a one-day aggregate snapshot,
not individual five-minute attack observations.

## 7.2 Refresh strategy

The system should treat the one-day Radar response as an observation
dataset.

A refresh creates a new observation.

Do not pretend that every synthetic visual event represents a newly
observed Cloudflare attack.

The globe can continuously animate the current observation dataset.

## 7.3 Observation metadata

Preserve:

-   collection time
-   source window start
-   source window end
-   Cloudflare `lastUpdated`
-   layer
-   normalization
-   units

------------------------------------------------------------------------

# 8. Normalization Architecture

Normalization is a strict boundary between Cloudflare's API format and
our application's internal format.

``` text
Cloudflare JSON
      │
      ▼
Cloudflare Adapter
      │
      ├── validate
      ├── parse
      ├── convert percentages
      └── preserve metadata
      │
      ▼
Canonical Domain Models
      │
      ├── AttackPair
      ├── DistributionEntry
      ├── AttackCharacteristic
      └── TimeSeriesPoint
      │
      ├───────────────┐
      ▼               ▼
PostgreSQL        Simulator
```

## 8.1 Percentage conversion

Cloudflare returns percentage values as strings on a 0--100 scale.

Example:

``` text
"6.844203"
```

means:

``` text
6.844203%
```

The canonical application representation is:

``` text
0.06844203
```

Therefore:

``` text
share = Decimal(raw_value) / 100
```

The canonical share range is:

``` text
0 <= share <= 1
```

## 8.2 Do not normalize timeseries the same way

Timeseries values use:

``` text
MIN0_MAX
```

They are already relative values.

Do not divide them by 100.

Do not label them as percentages.

Do not convert them into traffic volumes.

------------------------------------------------------------------------

# 9. Canonical Domain Models

These models are the internal language of the application.

They must not mirror Cloudflare's JSON field names unnecessarily.

## 9.1 AttackPair

Conceptual fields:

``` text
id
observation_id
layer
source_country_code
source_country_name
target_country_code
target_country_name
share
rank
unit
```

Rules:

-   `layer` is L3 or L7.
-   `share` is 0--1.
-   `rank` is optional.
-   `unit` is bytes for L3 and requests for L7.
-   source and target are independent countries.
-   self-pairs such as US → US are valid if Radar provides them.

## 9.2 DistributionEntry

Used for origin and target rankings.

Fields:

``` text
id
observation_id
layer
role
country_code
country_name
share
rank
unit
```

`role`:

``` text
origin
target
```

Rules:

-   origin data does not create attack pairs.
-   target data does not create attack pairs.
-   share is 0--1.

## 9.3 AttackCharacteristic

Fields:

``` text
id
observation_id
layer
category
value
share
unit
```

Categories:

``` text
protocol
vector
http_method
```

Rules:

-   protocol is L3.
-   vector is L3.
-   HTTP method is L7.
-   share is 0--1.
-   units must remain associated with the layer.

## 9.4 TimeSeriesPoint

Fields:

``` text
id
observation_id
layer
timestamp
value
normalization
unit
```

Rules:

``` text
normalization = MIN0_MAX
```

Value is a relative intensity value.

------------------------------------------------------------------------

# 10. Database Design

PostgreSQL stores durable Radar observations and analytics data.

It does not store every synthetic globe particle.

## 10.1 `radar_observations`

Purpose:

-   identify a collected Radar dataset
-   store observation metadata

Conceptual fields:

``` text
id
collected_at
window_start
window_end
last_updated
```

Potentially preserve:

``` text
layer
```

at observation level if the implementation chooses one observation per
layer.

## 10.2 `attack_pairs`

Purpose:

-   durable normalized source-to-target relationships

Fields:

``` text
id
observation_id
layer
source_country_code
source_country_name
target_country_code
target_country_name
share
rank
unit
```

## 10.3 `country_distributions`

Purpose:

-   origins
-   targets

Fields:

``` text
id
observation_id
layer
role
country_code
country_name
share
rank
unit
```

## 10.4 `attack_characteristics`

Purpose:

-   protocols
-   vectors
-   HTTP methods

Fields:

``` text
id
observation_id
layer
category
value
share
unit
```

## 10.5 `timeseries_points`

Purpose:

-   historical chart data

Fields:

``` text
id
observation_id
layer
timestamp
value
normalization
unit
```

## 10.6 Do not create `synthetic_events`

Synthetic events are temporary visualization state.

Do not persist:

-   every particle
-   every arc
-   every generated timestamp
-   every synthetic coordinate

The simulator should generate and recycle these in memory.

------------------------------------------------------------------------

# 11. Weighted Sampling

Weighted sampling is the bridge between real aggregate shares and
synthetic visual events.

## 11.1 What it means

Suppose normalized Radar data contains:

``` text
US → India       0.23
China → USA      0.18
Russia → Germany 0.12
```

The simulator treats these shares as route weights.

A route with a larger share is selected more often.

## 11.2 Important distinction

The Radar value is a:

``` text
share
```

The simulator uses that share as a:

``` text
sampling weight
```

Do not rename the stored Radar meaning to `probability`.

## 11.3 Sampling unit

The **attack pair is the sampling unit**.

Do not:

``` text
choose origin
then invent target
```

Instead:

``` text
choose complete edge

US → India
US → Germany
US → Japan
China → USA
...
```

This preserves actual observed relationships.

## 11.4 Example

If:

``` text
US → India = 23%
US → Germany = 8%
US → Japan = 5%
```

then US can visually attack multiple countries.

The simulator may repeatedly sample:

``` text
US → India
US → Japan
US → India
US → Germany
US → India
...
```

The globe therefore represents a weighted directed attack graph.

------------------------------------------------------------------------

# 12. Weighted Directed Graph Model

The normalized attack-pair dataset can be understood as:

``` text
Country = node
AttackPair = directed edge
Share = edge weight
```

Example:

``` text
US ──23%──→ India
US ── 8%──→ Germany
US ── 5%──→ Japan
CN ──18%──→ US
BR ── 7%──→ US
```

This naturally supports:

-   one country attacking many countries
-   many countries attacking one country
-   many-to-many global activity
-   self-pairs
-   multiple simultaneous routes

The globe should visualize this graph, not invent a separate
relationship model.

------------------------------------------------------------------------

# 13. Handling Top-N Data

The top attack endpoint returns a limited number of records.

The returned shares do not necessarily sum to 1.

Example:

``` text
US → India       0.23
China → USA      0.18
Russia → Germany 0.12
```

Total:

``` text
0.53
```

Do not automatically renormalize this to:

``` text
0.434
0.340
0.226
```

That would change the meaning of the Radar shares.

Preserve the original shares.

## 13.1 Remainder

The unrepresented remainder should be treated as:

``` text
other activity
```

until a specific implementation strategy is defined.

Do not fabricate detailed source-target pairs for the remainder merely
to make the numbers sum to 100%.

------------------------------------------------------------------------

# 14. Geographic Synthesis

Cloudflare gives country codes and country names.

It does not give us the individual attack coordinates required by the
globe.

Therefore geographic coordinates are generated separately.

## 14.1 Country point pools

Each relevant country gets a small synthetic point pool.

Initial target:

``` text
5–8 points per country
```

This is a visualization parameter, not a claim about the number of real
attack sources.

Example:

``` text
USA
 ├── U1
 ├── U2
 ├── U3
 ├── U4
 ├── U5
 └── U6

India
 ├── I1
 ├── I2
 ├── I3
 ├── I4
 ├── I5
 └── I6
```

## 14.2 Point generation

Points must be generated inside the geographic boundary of the country.

Do not generate arbitrary latitude/longitude pairs across the entire
world.

## 14.3 Point reuse

Point pools are reusable.

Events can repeatedly use:

``` text
U3 → I5
U1 → I2
U4 → I5
U2 → I1
```

This creates visual density without creating hundreds of permanent
points.

------------------------------------------------------------------------

# 15. Active Event Budget

The globe must have a controlled maximum number of simultaneously
visible synthetic events.

Initial implementation target:

``` text
MAX_ACTIVE_EVENTS = 30–50
```

This is configurable.

The important rule is:

> A 23% route does not mean 23% of the screen becomes occupied by
> particles.

The share controls route selection frequency.

The active event budget controls how many events are visible
simultaneously.

------------------------------------------------------------------------

# 16. Synthetic Attack Event

A synthetic event is a temporary visual object.

Conceptual fields:

``` text
event_id
layer

source_country_code
source_country_name
target_country_code
target_country_name

source_lat
source_lon
target_lat
target_lon

intensity

created_at
expires_at

is_synthetic
source
```

Recommended attribution semantics:

``` text
source = cloudflare_radar
is_synthetic = true
```

Do not use a field combination that implies the generated event itself
was individually observed.

The underlying distribution is real. The visual event is synthetic.

------------------------------------------------------------------------

# 17. Event Generation Pipeline

``` text
Normalized AttackPairs
        │
        ▼
Weighted Route Sampler
        │
        ▼
Select complete edge
        │
        ▼
Get source country point pool
        │
        ▼
Get target country point pool
        │
        ▼
Select synthetic source point
        │
        ▼
Select synthetic target point
        │
        ▼
Generate visual timing
        │
        ▼
Generate controlled intensity
        │
        ▼
Create SyntheticAttackEvent
        │
        ▼
WebSocket broadcast
        │
        ▼
Three.js globe
```

------------------------------------------------------------------------

# 18. Event Scheduling

The scheduler continuously maintains the active event pool.

Pseudo-flow:

``` text
while simulator_is_running:

    remove expired events

    while active_events < MAX_ACTIVE_EVENTS:

        route = weighted_sample(attack_pairs)

        source_point = choose_point(route.source)
        target_point = choose_point(route.target)

        event = create_synthetic_event(
            route,
            source_point,
            target_point
        )

        add_to_active_pool(event)

        broadcast(event)

    sleep(short_interval)
```

The exact timing values should be tuned during frontend integration.

Do not hard-code visual timing assumptions into the domain models.

------------------------------------------------------------------------

# 19. Visual Intensity

Radar share should primarily control route selection frequency.

It may also influence visual intensity, but not linearly enough to
destroy visual balance.

Avoid:

``` text
23% = 23x brighter than 1%
```

Instead use a bounded mapping.

Conceptually:

``` text
share
  ↓
bounded intensity function
  ↓
0.3–1.0 visual intensity
```

The exact mapping belongs to the simulator/rendering layer.

------------------------------------------------------------------------

# 20. Globe Layers

The globe should have multiple visual layers.

## Layer 1: Country activity points

Small persistent synthetic geographic markers.

## Layer 2: Attack arcs

Represent selected source-to-target pairs.

## Layer 3: Moving particles

Travel along arcs.

## Layer 4: Impact/pulse

Brief visual effect at the target.

## Layer 5: Optional country emphasis

Use aggregate origin/target distributions for subtle country-level
emphasis.

Do not confuse this layer with individual attack locations.

------------------------------------------------------------------------

# 21. Multiple Routes From One Country

The globe must support:

``` text
US → India
US → Germany
US → Japan
US → Canada
```

simultaneously.

The route sampler chooses complete attack-pair edges.

Therefore one country naturally acts as a node with multiple outgoing
edges.

Example:

``` text
             Germany
                ↑
                │
                │
India ←──────── US ───────→ Japan
                │
                ↓
              Canada
```

Each edge has its own Radar share.

------------------------------------------------------------------------

# 22. Multiple Sources to One Country

Also support:

``` text
US → India
China → India
Brazil → India
Germany → India
```

The globe should visually support convergence on the same target.

This naturally follows from the directed graph model.

------------------------------------------------------------------------

# 23. REST API

The frontend consumes our FastAPI API.

The frontend must not directly depend on Cloudflare's response format.

Final API surface:

``` text
GET /api/v1/radar/overview
GET /api/v1/radar/attacks
GET /api/v1/radar/countries
GET /api/v1/radar/characteristics
GET /api/v1/radar/history
GET /api/v1/radar/status
GET /api/v1/health

WS /api/v1/ws/radar
```

------------------------------------------------------------------------

# 24. `GET /api/v1/radar/overview`

Purpose:

-   initial dashboard state
-   initial globe state
-   current observation metadata
-   top routes
-   top origins
-   top targets

Conceptual response:

``` json
{
  "observation": {
    "start": "...",
    "end": "...",
    "last_updated": "...",
    "collected_at": "..."
  },
  "layer": "L3",
  "top_routes": [],
  "top_origins": [],
  "top_targets": []
}
```

This endpoint is designed for initial page loading.

------------------------------------------------------------------------

# 25. `GET /api/v1/radar/attacks`

Purpose:

-   normalized source-to-target attack pairs

Query parameters:

``` text
layer=L3|L7
```

Conceptual response:

``` json
{
  "layer": "L3",
  "unit": "bytes",
  "entries": [
    {
      "source": {
        "code": "BR",
        "name": "Brazil"
      },
      "target": {
        "code": "US",
        "name": "United States"
      },
      "share": 0.06844203,
      "rank": null
    }
  ]
}
```

This endpoint is the primary input for the route simulator.

------------------------------------------------------------------------

# 26. `GET /api/v1/radar/countries`

Purpose:

-   origin ranking
-   target ranking

Query parameters:

``` text
layer=L3|L7
role=origin|target
```

Conceptual response:

``` json
{
  "layer": "L3",
  "role": "origin",
  "unit": "bytes",
  "entries": [
    {
      "country": {
        "code": "US",
        "name": "United States"
      },
      "share": 0.1649431,
      "rank": 1
    }
  ]
}
```

------------------------------------------------------------------------

# 27. `GET /api/v1/radar/characteristics`

Purpose:

-   protocol distribution
-   vector distribution
-   HTTP method distribution

Query parameters:

``` text
layer=L3|L7
type=protocol|vector|http_method
```

Valid combinations:

``` text
L3 + protocol
L3 + vector
L7 + http_method
```

Conceptual response:

``` json
{
  "layer": "L3",
  "type": "protocol",
  "unit": "bytes",
  "entries": [
    {
      "value": "UDP",
      "share": 0.76322904
    }
  ]
}
```

------------------------------------------------------------------------

# 28. `GET /api/v1/radar/history`

Purpose:

-   historical chart

Query:

``` text
layer=L3|L7
```

Conceptual response:

``` json
{
  "layer": "L3",
  "unit": "bytes",
  "normalization": "MIN0_MAX",
  "aggregation": "ONE_HOUR",
  "points": [
    {
      "timestamp": "2026-08-15T05:00:00Z",
      "value": 0.112243
    }
  ]
}
```

The UI must label this as relative activity/intensity.

------------------------------------------------------------------------

# 29. `GET /api/v1/radar/status`

Purpose:

-   current dataset status
-   collection timestamp
-   observation window
-   Cloudflare update timestamp
-   cache/database health

Conceptual response:

``` json
{
  "status": "healthy",
  "observation_start": "...",
  "observation_end": "...",
  "last_updated": "...",
  "collected_at": "..."
}
```

------------------------------------------------------------------------

# 30. `GET /api/v1/health`

Purpose:

-   deployment health
-   service health checks

Response:

``` json
{
  "status": "ok"
}
```

Keep it boring.

------------------------------------------------------------------------

# 31. WebSocket

Endpoint:

``` text
WS /api/v1/ws/radar
```

Purpose:

-   stream synthetic visualization events
-   send simulation statistics
-   send system state changes

The WebSocket is not a replacement for REST.

REST provides durable/current data.

WebSocket provides temporary simulation events.

------------------------------------------------------------------------

# 32. WebSocket Message Envelope

All messages use a common envelope:

``` text
WebSocketMessage
├── type
└── data
```

Initial message types:

``` text
attack_event
stats
system
```

## 32.1 `attack_event`

``` json
{
  "type": "attack_event",
  "data": {
    "event_id": "...",
    "layer": "L3",
    "source": {
      "code": "US",
      "name": "United States",
      "lat": 0.0,
      "lon": 0.0
    },
    "target": {
      "code": "IN",
      "name": "India",
      "lat": 0.0,
      "lon": 0.0
    },
    "intensity": 0.72,
    "is_synthetic": true,
    "source": "cloudflare_radar"
  }
}
```

Coordinates in this event are synthetic.

## 32.2 `stats`

Example:

``` json
{
  "type": "stats",
  "data": {
    "active_events": 34
  }
}
```

## 32.3 `system`

Example:

``` json
{
  "type": "system",
  "data": {
    "message": "Radar dataset refreshed"
  }
}
```

------------------------------------------------------------------------

# 33. Frontend Architecture

Recommended structure:

``` text
frontend/
├── components/
│   ├── globe/
│   ├── analytics/
│   ├── history/
│   └── ui/
│
├── services/
│   ├── radar-api
│   └── radar-websocket
│
├── state/
│   └── radar-store
│
├── types/
│   └── radar
│
└── pages/
```

Use:

-   React
-   Three.js
-   WebGL
-   charting library of choice

The frontend receives normalized application contracts.

It must not parse Cloudflare JSON.

------------------------------------------------------------------------

# 34. Initial Page Load

Recommended flow:

``` text
Browser
   │
   ├── GET /overview
   ├── GET /characteristics
   ├── GET /history
   │
   ▼
Initialize UI
   │
   ▼
Connect WebSocket
   │
   ▼
Receive synthetic events
   │
   ▼
Animate globe
```

The globe should not wait for the first synthetic event before rendering
the base scene.

------------------------------------------------------------------------

# 35. Layer Switching

The application supports:

``` text
L3
L7
```

Layer selection must propagate through:

-   attack-pair data
-   origin data
-   target data
-   characteristics
-   history
-   simulator configuration

Never mix L3 and L7 measurements in one statistic.

Remember:

``` text
L3 = bytes
L7 = requests
```

------------------------------------------------------------------------

# 36. Analytics UI

## Top origins

Show:

``` text
country
share
rank
```

## Top targets

Show:

``` text
country
share
rank
```

## Protocols

Show:

``` text
UDP
TCP
GRE
ICMP
...
```

## Vectors

Show:

``` text
Mirai (UDP) Flood
SYN Flood
UDP Flood
...
```

## HTTP methods

Show:

``` text
GET
POST
HEAD
...
```

The UI should make the distinction between L3 and L7 obvious.

------------------------------------------------------------------------

# 37. Historical UI

The history section should show:

``` text
7-day activity
```

with:

``` text
L3 / L7
```

toggle.

The chart communicates relative activity.

Do not write:

``` text
10 Gbps
```

unless a future data source actually provides absolute volume.

The current Radar timeseries does not.

------------------------------------------------------------------------

# 38. Data Fetching Backend

The backend should have a dedicated Cloudflare client.

Conceptual structure:

``` text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── radar/
│   │   ├── client.py
│   │   ├── adapters/
│   │   │   ├── attacks.py
│   │   │   ├── locations.py
│   │   │   ├── characteristics.py
│   │   │   └── timeseries.py
│   │   └── models/
│   │       ├── external.py
│   │       └── normalized.py
│   │
│   ├── simulator/
│   │   ├── sampler.py
│   │   ├── geography.py
│   │   ├── scheduler.py
│   │   └── engine.py
│   │
│   └── websocket/
│       ├── manager.py
│       └── envelopes.py
│
└── tests/
```

Exact filenames can vary, but the boundaries should remain.

------------------------------------------------------------------------

# 39. Cloudflare Adapter Rules

The adapter is the only layer that should care about Cloudflare-specific
field names such as:

``` text
originCountryAlpha2
originCountryName
targetCountryAlpha2
targetCountryName
value
rank
```

The rest of the application should use:

``` text
source_country_code
source_country_name
target_country_code
target_country_name
share
rank
```

This protects the rest of the system from API-specific structure.

------------------------------------------------------------------------

# 40. Validation Rules

Every Radar response must be validated.

Minimum checks:

``` text
success == true
errors is empty
expected result key exists
expected records exist
percentage values are parseable
percentage values are within valid range
country codes are valid format
layer matches expected endpoint
unit matches expected layer
```

If a response is malformed:

-   do not silently invent values
-   do not create fake records
-   log the failure
-   preserve the last known good dataset if appropriate
-   expose stale/failed state through status

------------------------------------------------------------------------

# 41. Decimal Handling

Cloudflare percentage strings should be parsed using:

``` text
Decimal
```

or a carefully validated float.

Preferred behavior:

``` text
raw string
    ↓
Decimal
    ↓
divide by 100
    ↓
canonical share
```

Do not use string concatenation or ad-hoc parsing.

------------------------------------------------------------------------

# 42. Observation Ingestion

The ingestion pipeline:

``` text
Cloudflare
    ↓
HTTP request
    ↓
validate response
    ↓
adapter
    ↓
normalized domain objects
    ↓
database transaction
```

A failed endpoint must not produce a partially corrupted dataset.

Where practical, write a complete observation as one logical ingestion
unit.

------------------------------------------------------------------------

# 43. Caching

The backend may cache the current normalized observation.

Possible implementation:

``` text
PostgreSQL = durable source
Redis = optional fast current-state cache
```

Redis is not the source of truth.

If Redis is unavailable, the application should be able to recover
current data from PostgreSQL.

Do not use Redis to persist the synthetic event history.

------------------------------------------------------------------------

# 44. Synthetic Engine State

Synthetic state belongs in process memory or another temporary runtime
store.

Required state:

``` text
current attack-pair distribution
country point pools
active event pool
simulation configuration
```

The engine should be restartable.

Restarting the backend may produce a different synthetic event sequence.
That is acceptable.

The underlying Radar observation remains unchanged.

------------------------------------------------------------------------

# 45. Geographic Data

The geographic layer needs country boundaries or a reliable country
geometry dataset.

The country code from Radar is the join key.

Example:

``` text
US → United States geometry
IN → India geometry
DE → Germany geometry
```

Synthetic points must be sampled within the country geometry.

Do not derive precise real attack locations.

------------------------------------------------------------------------

# 46. Point Sampling Strategy

Initial strategy:

1.  Identify countries appearing in relevant attack pairs.
2.  Load their geographic polygons.
3.  Generate a small stable pool of points.
4.  Store the pool in simulator memory.
5.  Reuse those points across synthetic events.

The point pool is visual infrastructure.

It is not attack telemetry.

------------------------------------------------------------------------

# 47. Route Sampling Strategy

For every attack-pair observation:

``` text
AttackPair.share
```

becomes the route's sampling weight.

The simulator performs weighted sampling over complete pairs.

Example:

``` text
BR → US = 0.0684
US → US = 0.0463
US → CN = 0.0443
...
```

A route with 0.0684 should be selected more frequently than a route with
0.0443, all else equal.

------------------------------------------------------------------------

# 48. Active Event Recycling

The event lifecycle:

``` text
spawn
  ↓
animate
  ↓
arrive
  ↓
brief impact
  ↓
expire
  ↓
remove
  ↓
new event
```

The engine should continuously recycle the visual population.

Do not create an ever-growing event list.

------------------------------------------------------------------------

# 49. Performance Rules

The globe should prioritize:

1.  smooth animation
2.  bounded object count
3.  predictable memory usage
4.  low WebSocket payload size

Avoid:

-   sending full Radar datasets on every event
-   sending unnecessary geometry repeatedly
-   persisting every particle
-   creating thousands of simultaneous Three.js objects

Prefer:

-   reusable geometries
-   reusable materials
-   object pooling where appropriate
-   bounded event counts
-   compact WebSocket messages

------------------------------------------------------------------------

# 50. API Separation

Cloudflare:

``` text
external API
```

Our FastAPI:

``` text
application API
```

Frontend:

``` text
consumer
```

Never allow:

``` text
Frontend → Cloudflare directly
```

The backend owns:

-   authentication token
-   API calls
-   normalization
-   caching
-   persistence
-   simulation

------------------------------------------------------------------------

# 51. Error Handling

## Cloudflare failure

If a fetch fails:

``` text
do not overwrite last good observation
```

Expose:

``` text
status = degraded
```

and retain the last known dataset if available.

## Database failure

The API should fail clearly rather than fabricate data.

## WebSocket failure

Frontend reconnects.

On reconnect:

1.  obtain current state if required
2.  reconnect WebSocket
3.  resume simulation stream

## Invalid Radar data

Reject the affected response.

Do not silently coerce invalid values into plausible-looking data.

------------------------------------------------------------------------

# 52. Testing Strategy

Testing should happen at every boundary.

## 52.1 Adapter tests

Use the captured Radar samples.

Test:

-   successful response parsing
-   percentage conversion
-   optional rank
-   country fields
-   units
-   metadata
-   timeseries arrays

## 52.2 Normalization tests

Verify:

``` text
"6.844203" → 0.06844203
```

Verify L3:

``` text
unit = bytes
```

Verify L7:

``` text
unit = requests
```

Verify timeseries:

``` text
normalization = MIN0_MAX
```

and verify it is not treated as a percentage.

## 52.3 Simulator tests

Test:

-   weighted sampling
-   route selection
-   multiple targets from one origin
-   multiple origins to one target
-   self-pairs
-   active event limit
-   event expiration
-   point-pool reuse

## 52.4 API tests

Test:

-   response contracts
-   query validation
-   L3/L7 separation
-   missing observations
-   degraded status

## 52.5 WebSocket tests

Test:

-   connection
-   message envelope
-   attack event schema
-   stats message
-   reconnect behavior

------------------------------------------------------------------------

# 53. Statistical Testing of Weighted Sampling

Weighted sampling should not be tested by expecting a tiny sample to
exactly match the source percentages.

Instead:

1.  run a large synthetic sample
2.  count selected routes
3.  compare observed synthetic frequencies to source shares
4.  allow reasonable statistical variation

Example:

``` text
Radar:
US → India = 0.23

Synthetic sample:
approximately 23% of route selections
```

The synthetic sequence is random.

Exact equality on every batch is not required.

------------------------------------------------------------------------

# 54. Contract Testing

The captured Cloudflare sample responses are fixtures.

They should be committed to the repository as test fixtures.

Recommended structure:

``` text
tests/
└── fixtures/
    └── radar/
        ├── layer3-top-attacks.json
        ├── layer7-top-attacks.json
        ├── layer3-top-origin.json
        ├── layer3-top-target.json
        ├── layer7-top-origin.json
        ├── layer7-top-target.json
        ├── layer3-summary-protocol.json
        ├── layer3-summary-vector.json
        ├── layer7-summary-http-method.json
        ├── layer3-timeseries.json
        └── layer7-timeseries.json
```

The actual raw responses should remain the source of truth for adapter
tests.

------------------------------------------------------------------------

# 55. Implementation Phases

## Phase 1 --- Repository and contracts

Build:

-   project structure
-   configuration
-   Pydantic models
-   database models
-   Cloudflare external models
-   normalized domain models
-   API response models
-   WebSocket envelope models

Do not build the globe yet.

## Phase 2 --- Cloudflare ingestion

Build:

-   Cloudflare client
-   endpoint methods
-   adapters
-   validation
-   normalization
-   database ingestion

Verify all 11 endpoints.

## Phase 3 --- Database

Build:

-   migrations
-   tables
-   indexes
-   observation persistence
-   normalized records

Verify data can be queried without Cloudflare.

## Phase 4 --- Analytics API

Build:

-   overview
-   attacks
-   countries
-   characteristics
-   history
-   status
-   health

At this stage the frontend can consume real normalized data.

## Phase 5 --- Geography

Build:

-   country-code lookup
-   country geometry
-   synthetic point generation
-   stable point pools

## Phase 6 --- Synthetic engine

Build:

-   weighted route sampler
-   event scheduler
-   active-event pool
-   timing
-   intensity
-   event recycling

Test statistically.

## Phase 7 --- WebSocket

Build:

-   connection manager
-   event broadcast
-   stats messages
-   system messages
-   reconnect behavior

## Phase 8 --- Globe

Build:

-   Three.js globe
-   country rendering
-   point rendering
-   arcs
-   moving particles
-   impact effects
-   active-event rendering

## Phase 9 --- Analytics UI

Build:

-   top origins
-   top targets
-   protocols
-   vectors
-   HTTP methods

## Phase 10 --- History UI

Build:

-   seven-day L3 chart
-   seven-day L7 chart
-   layer switch
-   correct relative-intensity labels

## Phase 11 --- Polish

Build:

-   loading states
-   error states
-   stale-data indicator
-   responsive layout
-   visual hierarchy
-   performance tuning

------------------------------------------------------------------------

# 56. Development Order

The implementation order is intentionally:

``` text
REAL DATA
   ↓
CONTRACTS
   ↓
NORMALIZATION
   ↓
DATABASE
   ↓
REST API
   ↓
GEOGRAPHY
   ↓
SIMULATOR
   ↓
WEBSOCKET
   ↓
GLOBE
   ↓
ANALYTICS UI
   ↓
HISTORY UI
   ↓
POLISH
```

Do not start with the globe.

The globe is the most visible component, but the data contract is the
foundation.

------------------------------------------------------------------------

# 57. Definition of Done

The project is complete when:

## Data

-   all 11 Radar endpoints can be fetched
-   all responses are validated
-   percentage values are converted to 0--1 shares
-   L3/L7 units are preserved
-   timeseries `MIN0_MAX` semantics are preserved
-   source/target pair relationships are preserved

## Database

-   observations are persisted
-   attack pairs are persisted
-   country distributions are persisted
-   characteristics are persisted
-   timeseries points are persisted
-   synthetic events are not persisted

## Simulator

-   routes are weighted by Radar shares
-   multiple destinations per origin work
-   multiple origins per target work
-   self-pairs work
-   country point pools remain small
-   points remain inside country geometry
-   active events are bounded
-   events are recycled

## WebSocket

-   events stream correctly
-   envelope is validated
-   reconnect works
-   stats are available

## Globe

-   globe renders smoothly
-   arcs render correctly
-   particles move
-   multiple routes can coexist
-   target impacts render
-   high-share routes appear more frequently
-   the globe does not become overloaded

## Analytics

-   origins are shown
-   targets are shown
-   protocols are shown
-   vectors are shown
-   HTTP methods are shown

## History

-   seven-day L3 data is shown
-   seven-day L7 data is shown
-   relative-intensity semantics are clear

------------------------------------------------------------------------

# 58. Non-Negotiable Rules

1.  **Never invent missing Cloudflare data.**
2.  **Never reconstruct source-target pairs from separate origin/target
    distributions.**
3.  **Never treat a synthetic event as an individually observed
    attack.**
4.  **Never interpret `MIN0_MAX` timeseries values as absolute traffic
    volume.**
5.  **Never combine L3 bytes and L7 requests into one statistic.**
6.  **Never turn a 23% route into 230 simultaneous visual points.**
7.  **Never generate arbitrary global coordinates for a country-specific
    event.**
8.  **Never let frontend code depend on Cloudflare's raw JSON format.**
9.  **Never persist every synthetic particle.**
10. **Never silently replace missing/invalid Radar data with invented
    values.**
11. **Keep the attack pair as the fundamental route-sampling unit.**
12. **Keep real Radar observations separate from synthetic visualization
    state.**

------------------------------------------------------------------------

# 59. Final Architecture

``` text
                         CLOUDFLARE RADAR
                                │
                       11 configured endpoints
                                │
                                ▼
                       ┌─────────────────┐
                       │ Radar Client    │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Adapters        │
                       │ + Validation    │
                       └────────┬────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ Normalized Domain Data │
                    └────────────┬───────────┘
                                 │
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
            AttackPairs     Distributions   History
                  │              │              │
                  └──────────────┼──────────────┘
                                 ▼
                           PostgreSQL
                                 │
             ┌───────────────────┴───────────────────┐
             │                                       │
             ▼                                       ▼
       Analytics REST                         Synthetic Engine
                                                     │
                                    ┌────────────────┼───────────────┐
                                    ▼                ▼               ▼
                              Weighted routes   Geo points       Scheduler
                                    │                │               │
                                    └────────────────┼───────────────┘
                                                     ▼
                                           SyntheticAttackEvent
                                                     │
                                                     ▼
                                               WebSocket
                                                     │
                                                     ▼
                                                  🌍 Globe

             PostgreSQL / REST
                    │
                    ├──────────→ Analytics UI
                    │
                    └──────────→ History UI
```

------------------------------------------------------------------------

# 60. Final Mental Model

The entire project can be reduced to five ideas:

``` text
1. Cloudflare gives us aggregate truth.

2. We normalize that truth into clean internal models.

3. Attack pairs form a weighted directed graph.

4. Weighted sampling turns graph shares into synthetic visual events.

5. The globe visualizes those events while analytics/history show the actual
   aggregate data.
```

The project is therefore:

> **A statistically grounded, synthetic visualization of global DDoS
> activity using Cloudflare Radar aggregate telemetry.**

That is the implementation boundary.

Anything outside this definition should be treated as a future feature,
not part of the current build.
