create extension if not exists pgcrypto;

create table if not exists public.summary_jobs (
    id uuid primary key default gen_random_uuid(),
    status text not null,
    stage text not null,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    started_at timestamptz,
    completed_at timestamptz,
    source_filename text,
    mime_type text,
    duration_seconds double precision,
    summary_json jsonb,
    error_code text,
    error_message text
);

create index if not exists summary_jobs_status_idx on public.summary_jobs (status);
create index if not exists summary_jobs_updated_at_idx on public.summary_jobs (updated_at desc);
