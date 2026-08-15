# DDoS Attack Visualizer — Database Schema

## 1. Purpose

This document defines the PostgreSQL database schema for the DDoS Attack Visualizer.

The database is responsible for storing:

1. Normalized observations retrieved from Cloudflare Radar.
2. The normalized records derived from those observations (attack pairs, country distributions, attack characteristics, timeseries).

The database is **not** responsible for storing every synthetic WebSocket visualization event.

Live visualization events are generated in memory and broadcast through FastAPI WebSockets.

### Architecture

```text
Cloudflare Radar
       │
       ▼
  Radar Client + Adapters
       │
       ▼
  Radar Dataset (normalized)
       │
       ▼
  ObservationRepository (atomic refresh)
       │
       ▼
  PostgreSQL
       │
       ├── radar_observations
       ├── attack_pairs
       ├── country_distributions
       ├── attack_characteristics
       └── timeseries_points
       │
       ▼
  Weighted Distribution / Simulator
       │
       ▼
  FastAPI WebSocket
       │
       ▼
  Next.js Frontend
```

---

## 2. Database Technology

Database:

**PostgreSQL**

Provider:

**Supabase**

The Supabase project is used primarily as managed PostgreSQL infrastructure.

The FastAPI backend communicates with PostgreSQL using:

* SQLAlchemy 2.x
* asyncpg

The frontend does NOT connect directly to the database.

```text
Next.js
   │
   │ WebSocket / REST
   ▼
FastAPI
   │
   │ SQLAlchemy
   ▼
Supabase PostgreSQL
```

---

## 3. Database Tables

The schema contains five application tables:

```text
radar_observations
attack_pairs
country_distributions
attack_characteristics
timeseries_points
```

There are no user/authentication tables.

There is no `attacks` table for individual live events, and no `synthetic_events` table. Synthetic globe particles are never persisted.

---

## 4. Table: radar_observations

## Purpose

One row represents one endpoint response collected during a refresh.

A full refresh fetches all 11 endpoints. Every observation created in that refresh shares the same `refresh_id`.

## Columns

| Column                   | PostgreSQL Type | Nullable | Description                                   |
| ------------------------ | --------------- | -------: | --------------------------------------------- |
| id                       | uuid            |       NO | Primary key                                   |
| refresh_id               | uuid            |       NO | Groups all endpoint responses of one refresh  |
| endpoint_key             | text            |       NO | Endpoint identifier, e.g. `layer3-top-attacks`|
| layer                    | text            |       NO | Attack layer: L3 or L7                        |
| collected_at             | timestamptz     |       NO | Time the backend collected this response      |
| window_start             | timestamptz     |     YES  | Source window start from Radar `dateRange`    |
| window_end               | timestamptz     |     YES  | Source window end from Radar `dateRange`      |
| cloudflare_last_updated  | timestamptz     |     YES  | Radar `lastUpdated` for this response         |
| normalization            | text            |       NO | `PERCENTAGE` or `MIN0_MAX`                    |
| unit                     | text            |       NO | `bytes` (L3) or `requests` (L7)               |
| created_at               | timestamptz     |       NO | Database insertion timestamp                  |

### Unique constraint

```sql
constraint uq_radar_observations_refresh_endpoint
    unique (refresh_id, endpoint_key)
```

This makes a refresh idempotent per endpoint.

---

## 5. Table: attack_pairs

## Purpose

Durable normalized source-country to target-country relationships from the `top/attacks` endpoints.

## Columns

| Column               | PostgreSQL Type | Nullable | Description                       |
| -------------------- | --------------- | -------: | --------------------------------- |
| id                   | uuid            |       NO | Primary key                       |
| observation_id       | uuid            |       NO | FK to `radar_observations.id`     |
| layer                | text            |       NO | L3 or L7                          |
| source_country_code  | varchar(2)      |       NO | ISO alpha-2 (or `T1`) source code |
| source_country_name  | text            |     YES  | Source country name               |
| target_country_code  | varchar(2)      |       NO | Target country code               |
| target_country_name  | text            |     YES  | Target country name               |
| share                | numeric(10, 8)  |       NO | Share in [0, 1]                   |
| rank                 | integer         |     YES  | Optional rank (L3 pair data omits)|
| unit                 | text            |       NO | `bytes` or `requests`             |

### Notes

* Self-pairs such as US → US are valid if Radar provides them.
* `T1` is Cloudflare's Tor identifier and is accepted by the country-code check.
* `rank` is optional because Layer 3 pair responses do not include it.

---

## 6. Table: country_distributions

## Purpose

Country-level origin and target rankings from the `top/locations` endpoints.

Origin and target records are stored separately via the `role` column. They are never combined to reconstruct source-to-target pairs.

## Columns

| Column          | PostgreSQL Type | Nullable | Description                        |
| --------------- | --------------- | -------: | ---------------------------------- |
| id              | uuid            |       NO | Primary key                        |
| observation_id  | uuid            |       NO | FK to `radar_observations.id`      |
| layer           | text            |       NO | L3 or L7                           |
| role            | text            |       NO | `origin` or `target`               |
| country_code    | varchar(2)      |       NO | Country code                       |
| country_name    | text            |     YES  | Country name                       |
| share           | numeric(10, 8)  |       NO | Share in [0, 1]                    |
| rank            | integer         |     YES  | Rank                               |
| unit            | text            |       NO | `bytes` or `requests`              |

---

## 7. Table: attack_characteristics

## Purpose

Protocol, attack-vector, and HTTP-method distributions from the `summary` endpoints.

## Columns

| Column          | PostgreSQL Type | Nullable | Description                                 |
| --------------- | --------------- | -------: | ------------------------------------------- |
| id              | uuid            |       NO | Primary key                                 |
| observation_id  | uuid            |       NO | FK to `radar_observations.id`               |
| layer           | text            |       NO | L3 or L7                                    |
| category        | text            |       NO | `protocol`, `vector`, or `http_method`      |
| value           | text            |       NO | e.g. `UDP`, `SYN Flood`, `GET`              |
| share           | numeric(10, 8)  |       NO | Share in [0, 1]                             |
| unit            | text            |       NO | `bytes` or `requests`                       |

Valid combinations:

```text
L3 + protocol
L3 + vector
L7 + http_method
```

---

## 8. Table: timeseries_points

## Purpose

Historical seven-day relative activity from the `timeseries` endpoints.

## Columns

| Column          | PostgreSQL Type  | Nullable | Description                       |
| --------------- | ---------------- | -------: | --------------------------------- |
| id              | uuid             |       NO | Primary key                       |
| observation_id  | uuid             |       NO | FK to `radar_observations.id`     |
| layer           | text             |       NO | L3 or L7                          |
| timestamp       | timestamptz      |       NO | Point timestamp                   |
| value           | double precision |       NO | Relative value in [0, 1]          |
| normalization   | text             |       NO | Always `MIN0_MAX`                 |
| unit            | text             |       NO | `bytes` or `requests`             |

### Important

Timeseries values use `MIN0_MAX` normalization. They are relative intensity values.

They must never be presented as:

```text
Mbps
packets per second
absolute bytes
absolute request counts
```

---

## 9. Constraints

### Layer

```sql
check (layer in ('L3', 'L7'))
```

### Country codes

Country codes must be exactly two uppercase alphanumeric characters.

```sql
check (source_country_code ~ '^[A-Z0-9]{2}$')
```

This permits ISO alpha-2 codes and Cloudflare's `T1` (Tor) identifier.

### Share

```sql
check (share >= 0 and share <= 1)
```

### Rank

```sql
check (rank is null or rank > 0)
```

### Unit

```sql
check (unit in ('bytes', 'requests'))
```

### Normalization

```sql
check (normalization in ('PERCENTAGE', 'MIN0_MAX'))
```

### Foreign keys

Every child row references `radar_observations.id` with `on delete cascade`.

---

## 10. Indexes

Created per table to support analytics queries:

```text
radar_observations
  idx_radar_observations_refresh_id
  idx_radar_observations_layer_collected_at

attack_pairs
  idx_attack_pairs_observation_id
  idx_attack_pairs_observation_layer_share

country_distributions
  idx_country_distributions_observation_id
  idx_country_distributions_layer_role_share

attack_characteristics
  idx_attack_characteristics_observation_id
  idx_attack_characteristics_layer_category_share

timeseries_points
  idx_timeseries_points_observation_id
  idx_timeseries_points_observation_timestamp
```

---

## 11. Row Level Security

RLS is enabled on all five tables.

There are currently **no public client policies**.

The frontend does not need direct database access.

The backend is the only data-access layer.

---

## 12. Database Access Model

```text
                   INTERNET
                       │
                       ▼
                Next.js Frontend
                       │
                REST / WebSocket
                       │
                       ▼
                 FastAPI Backend
                       │
                 SQLAlchemy
                       │
                       ▼
              Supabase PostgreSQL
```

The browser never receives:

```text
DATABASE_URL
service_role key
CF_API_TOKEN
```

---

## 13. Live WebSocket Events Are NOT Stored

This is a critical architectural rule.

Synthetic visualization events are:

```text
generated
   ↓
broadcast
   ↓
expire
```

They are never written to PostgreSQL.

The database stores the normalized aggregated observations that drive the visualization.

---

## 14. Migrations

Schema changes are migration-based.

Every schema change must be:

```text
migration
    ↓
test
    ↓
application update
```

Current migrations:

```text
supabase/migrations/20260813103821_create_ddos_schema.sql      (legacy two-table schema)
supabase/migrations/20260815122113_create_normalized_schema.sql (normalized schema)
```

The `attack_snapshots` table from the legacy migration was retired in the normalized migration.

---

## 15. Expected Database Queries

The schema supports these analytics operations.

### Latest observation for an endpoint + layer

```sql
select *
from public.radar_observations
where endpoint_key = 'layer3-top-attacks'
  and layer = 'L3'
order by collected_at desc
limit 1;
```

### Top attack pairs for the latest observation

```sql
select p.source_country_code, p.target_country_code, p.share
from public.attack_pairs p
join public.radar_observations o on o.id = p.observation_id
where o.endpoint_key = 'layer3-top-attacks'
order by o.collected_at desc, p.share desc
limit 100;
```

### Top origins / targets

```sql
select d.country_code, d.share, d.rank
from public.country_distributions d
join public.radar_observations o on o.id = d.observation_id
where o.layer = 'L3' and d.role = 'origin'
order by o.collected_at desc, d.share desc;
```

### Characteristics

```sql
select c.category, c.value, c.share
from public.attack_characteristics c
join public.radar_observations o on o.id = c.observation_id
where o.layer = 'L7' and c.category = 'http_method'
order by o.collected_at desc, c.share desc;
```

### History

```sql
select t.timestamp, t.value
from public.timeseries_points t
join public.radar_observations o on o.id = t.observation_id
where o.layer = 'L3'
order by o.collected_at desc, t.timestamp;
```

---

## 16. Definition of Done

The database foundation is complete when:

* [ ] Supabase project created and linked
* [ ] All five normalized tables created
* [ ] Constraints created
* [ ] Indexes created
* [ ] RLS enabled
* [ ] Migration committed
* [ ] Live integration tests pass
* [ ] A real Radar refresh persists and can be queried without Cloudflare
