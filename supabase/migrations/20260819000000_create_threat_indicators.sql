-- Threat Observatory: real threat indicators from public feeds.
--
-- Rows are populated by the ThreatIntelIngestor from abuse.ch URLhaus,
-- Feodo Tracker, and ThreatFox (optionally enriched with GreyNoise
-- Community). Each row is a real IOC observed within the retention window;
-- older rows are pruned by a background task (default 7 days).
--
-- The dedup key is (source_feed, indicator): the same IOC re-observed by a
-- later poll updates last_seen rather than inserting a duplicate.

create table public.threat_indicators (
    id uuid primary key default gen_random_uuid(),

    source_feed text not null
        check (source_feed in ('urlhaus', 'feodo', 'threatfox')),

    indicator text not null,
    indicator_type text not null
        check (indicator_type in ('url', 'ip', 'domain')),

    resolved_ip text not null,

    country_code varchar(2)
        check (country_code is null or country_code ~ '^[A-Z0-9]{2}$'),
    country_name text,
    city text,
    latitude double precision,
    longitude double precision,

    threat_family text,

    first_seen timestamptz not null,
    last_seen timestamptz not null,

    greynoise_classification text,
    greynoise_tags text,

    source_url text,

    created_at timestamptz not null default now(),

    constraint uq_threat_indicators_feed_indicator
        unique (source_feed, indicator)
);

create index idx_threat_indicators_last_seen
    on public.threat_indicators (last_seen desc);

create index idx_threat_indicators_created_at
    on public.threat_indicators (created_at desc);

create index idx_threat_indicators_source_feed_last_seen
    on public.threat_indicators (source_feed, last_seen desc);

create index idx_threat_indicators_country_code
    on public.threat_indicators (country_code)
    where country_code is not null;

-- Row Level Security — matches the pattern used by the other tables. The
-- backend is the only data-access layer; no public client policies exist.
alter table public.threat_indicators enable row level security;
