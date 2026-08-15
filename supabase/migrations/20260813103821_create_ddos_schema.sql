create extension if not exists pgcrypto;

create table public.radar_observations (
    id uuid primary key default gen_random_uuid(),

    observed_at timestamptz not null,

    layer text not null
        check (layer in ('L3', 'L7')),

    source_country char(2) not null
        check (source_country ~ '^[A-Z]{2}$'),

    target_country char(2) not null
        check (target_country ~ '^[A-Z]{2}$'),

    attack_share double precision not null
        check (attack_share >= 0 and attack_share <= 1),

    rank integer not null
        check (rank > 0),

    created_at timestamptz not null default now()
);


create table public.attack_snapshots (
    id uuid primary key default gen_random_uuid(),

    captured_at timestamptz not null,

    layer text not null
        check (layer in ('L3', 'L7')),

    source_country char(2) not null
        check (source_country ~ '^[A-Z]{2}$'),

    target_country char(2) not null
        check (target_country ~ '^[A-Z]{2}$'),

    attack_share double precision not null
        check (attack_share >= 0 and attack_share <= 1),

    created_at timestamptz not null default now()
);


create index idx_radar_observations_observed_at
on public.radar_observations (observed_at desc);


create index idx_radar_observations_layer_observed_at
on public.radar_observations (layer, observed_at desc);


create index idx_radar_observations_source_country
on public.radar_observations (source_country);


create index idx_radar_observations_target_country
on public.radar_observations (target_country);


create index idx_attack_snapshots_captured_at
on public.attack_snapshots (captured_at desc);


create index idx_attack_snapshots_layer_captured_at
on public.attack_snapshots (layer, captured_at desc);


alter table public.radar_observations enable row level security;

alter table public.attack_snapshots enable row level security;
