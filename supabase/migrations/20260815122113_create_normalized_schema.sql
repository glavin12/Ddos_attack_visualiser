-- Phase 3: normalized Radar observation schema.
--
-- Replaces the original two-table schema (radar_observations + attack_snapshots)
-- with the normalized model defined by IMPLEMENTATION.md section 10:
--
--   radar_observations      - one row per endpoint response, grouped by refresh_id
--   attack_pairs            - durable source -> target relationships (top/attacks)
--   country_distributions   - origin/target rankings (top/locations)
--   attack_characteristics  - protocol/vector/http_method summaries
--   timeseries_points       - MIN0_MAX historical points
--
-- Synthetic globe particles are never persisted.

-- ---------------------------------------------------------------------------
-- Drop the legacy two-table schema. Both tables are empty in this project's
-- history; radar_observations is recreated with the new metadata shape.
-- ---------------------------------------------------------------------------

drop table if exists public.attack_snapshots;

drop table if exists public.radar_observations;

-- ---------------------------------------------------------------------------
-- radar_observations
-- ---------------------------------------------------------------------------

create table public.radar_observations (
    id uuid primary key default gen_random_uuid(),

    refresh_id uuid not null,
    endpoint_key text not null,

    layer text not null
        check (layer in ('L3', 'L7')),

    collected_at timestamptz not null,
    window_start timestamptz,
    window_end timestamptz,
    cloudflare_last_updated timestamptz,

    normalization text not null
        check (normalization in ('PERCENTAGE', 'MIN0_MAX')),

    unit text not null
        check (unit in ('bytes', 'requests')),

    created_at timestamptz not null default now(),

    constraint uq_radar_observations_refresh_endpoint
        unique (refresh_id, endpoint_key)
);

create index idx_radar_observations_refresh_id
    on public.radar_observations (refresh_id);

create index idx_radar_observations_layer_collected_at
    on public.radar_observations (layer, collected_at desc);

-- ---------------------------------------------------------------------------
-- attack_pairs
-- ---------------------------------------------------------------------------

create table public.attack_pairs (
    id uuid primary key default gen_random_uuid(),

    observation_id uuid not null
        references public.radar_observations (id) on delete cascade,

    layer text not null
        check (layer in ('L3', 'L7')),

    source_country_code varchar(2) not null
        check (source_country_code ~ '^[A-Z0-9]{2}$'),
    source_country_name text,

    target_country_code varchar(2) not null
        check (target_country_code ~ '^[A-Z0-9]{2}$'),
    target_country_name text,

    share numeric(10, 8) not null
        check (share >= 0 and share <= 1),

    rank integer
        check (rank is null or rank > 0),

    unit text not null
        check (unit in ('bytes', 'requests')),

    constraint uq_attack_pairs_observation_src_tgt
        unique (observation_id, source_country_code, target_country_code)
);

create index idx_attack_pairs_observation_id
    on public.attack_pairs (observation_id);

create index idx_attack_pairs_observation_layer_share
    on public.attack_pairs (observation_id, layer, share desc);

-- ---------------------------------------------------------------------------
-- country_distributions
-- ---------------------------------------------------------------------------

create table public.country_distributions (
    id uuid primary key default gen_random_uuid(),

    observation_id uuid not null
        references public.radar_observations (id) on delete cascade,

    layer text not null
        check (layer in ('L3', 'L7')),

    role text not null
        check (role in ('origin', 'target')),

    country_code varchar(2) not null
        check (country_code ~ '^[A-Z0-9]{2}$'),
    country_name text,

    share numeric(10, 8) not null
        check (share >= 0 and share <= 1),

    rank integer
        check (rank is null or rank > 0),

    unit text not null
        check (unit in ('bytes', 'requests')),

    constraint uq_country_distributions_observation_role_country
        unique (observation_id, role, country_code)
);

create index idx_country_distributions_observation_id
    on public.country_distributions (observation_id);

create index idx_country_distributions_layer_role_share
    on public.country_distributions (layer, role, share desc);

-- ---------------------------------------------------------------------------
-- attack_characteristics
-- ---------------------------------------------------------------------------

create table public.attack_characteristics (
    id uuid primary key default gen_random_uuid(),

    observation_id uuid not null
        references public.radar_observations (id) on delete cascade,

    layer text not null
        check (layer in ('L3', 'L7')),

    category text not null
        check (category in ('protocol', 'vector', 'http_method')),

    value text not null,

    share numeric(10, 8) not null
        check (share >= 0 and share <= 1),

    unit text not null
        check (unit in ('bytes', 'requests')),

    constraint uq_attack_characteristics_observation_category_value
        unique (observation_id, category, value)
);

create index idx_attack_characteristics_observation_id
    on public.attack_characteristics (observation_id);

create index idx_attack_characteristics_layer_category_share
    on public.attack_characteristics (layer, category, share desc);

-- ---------------------------------------------------------------------------
-- timeseries_points
-- ---------------------------------------------------------------------------

create table public.timeseries_points (
    id uuid primary key default gen_random_uuid(),

    observation_id uuid not null
        references public.radar_observations (id) on delete cascade,

    layer text not null
        check (layer in ('L3', 'L7')),

    timestamp timestamptz not null,

    value double precision not null
        check (value >= 0 and value <= 1),

    normalization text not null
        check (normalization in ('PERCENTAGE', 'MIN0_MAX')),

    unit text not null
        check (unit in ('bytes', 'requests')),

    constraint uq_timeseries_points_observation_timestamp
        unique (observation_id, timestamp)
);

create index idx_timeseries_points_observation_id
    on public.timeseries_points (observation_id);

create index idx_timeseries_points_observation_timestamp
    on public.timeseries_points (observation_id, timestamp);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
--
-- The backend is the only data-access layer. There are intentionally no
-- public client policies, matching the documented access model.

alter table public.radar_observations enable row level security;
alter table public.attack_pairs enable row level security;
alter table public.country_distributions enable row level security;
alter table public.attack_characteristics enable row level security;
alter table public.timeseries_points enable row level security;
