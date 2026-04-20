-- ─────────────────────────────────────────────────────────────────────────────
-- Equity Guard — Supabase schema
-- Rode este script UMA VEZ no Supabase SQL Editor apos criar o projeto.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Tabela principal de usuarios
create table if not exists public.users (
    email         text primary key,
    is_admin      boolean not null default false,
    credits       integer not null default 10,   -- -1 = ilimitado (admin)
    queries_used  integer not null default 0,
    created_at    timestamptz not null default now(),
    last_login    timestamptz not null default now(),
    is_anonymous  boolean not null default false
);

-- 2. Favoritos (watchlist)
create table if not exists public.favorites (
    email       text not null references public.users(email) on delete cascade,
    ticker      text not null,
    created_at  timestamptz not null default now(),
    primary key (email, ticker)
);

-- 3. Historico de consultas
create table if not exists public.history (
    id           bigserial primary key,
    email        text not null references public.users(email) on delete cascade,
    ticker       text not null,
    accessed_at  timestamptz not null default now()
);
create index if not exists idx_history_email_time
    on public.history (email, accessed_at desc);

-- 4. Row Level Security — bloqueia acesso anonimo direto.
-- O backend usa SERVICE_ROLE_KEY que bypass RLS, entao continua funcionando.
alter table public.users     enable row level security;
alter table public.favorites enable row level security;
alter table public.history   enable row level security;

-- 5. Politica: anon nao acessa nada. service_role nao precisa de policy (bypassa).
-- Quando migrarmos para magic-link, adicionamos policies per-user.

-- Confirmacao
select 'Schema OK: users / favorites / history criados com RLS ativado' as status;
