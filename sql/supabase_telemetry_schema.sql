-- Her müşteri kendi Supabase projesinde bu tabloyu oluşturmalı.
create table if not exists public.telemetry (
  id bigserial primary key,
  device_id text not null,
  temperature numeric,
  humidity numeric,
  voltage numeric,
  created_at timestamptz not null default now()
);

-- Dashboard tarafında anon key ile okuma için RLS örneği (isteğe bağlı, projeye göre uyarlayın).
alter table public.telemetry enable row level security;

-- Demo policy: tüm satırları okunabilir yapar (üretimde daha sıkı politika önerilir)
drop policy if exists "anon_read_telemetry" on public.telemetry;
create policy "anon_read_telemetry"
  on public.telemetry
  for select
  to anon
  using (true);
