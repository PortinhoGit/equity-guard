-- ─────────────────────────────────────────────────────────────────────────────
-- Equity Guard — tabela de assinantes do briefing diario
-- Rode este script UMA VEZ no Supabase SQL Editor.
-- ─────────────────────────────────────────────────────────────────────────────

create table if not exists public.subscribers (
    email              text primary key,
    token              text not null unique,
    subscribed_at      timestamptz not null default now(),
    last_email_sent_at timestamptz,
    is_active          boolean not null default true
);

create index if not exists idx_subscribers_active
    on public.subscribers (is_active);

alter table public.subscribers enable row level security;

select 'OK: tabela subscribers criada com RLS ativado' as status;
