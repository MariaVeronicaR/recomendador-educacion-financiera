-- Migración: reescribir la tabla interactions con el esquema de eventos
-- del generador (view/started/completed/quiz_passed/quiz_failed + score).
-- Ejecutar en el SQL Editor de Supabase si ya creaste la tabla antigua
-- (interaction_type/completed/outcome). Los datos antiguos se descartan.
drop table if exists public.interactions;

create table public.interactions (
  id                 bigint generated always as identity primary key,
  user_id            uuid references auth.users (id) on delete cascade,
  content_id         text not null,
  event              text not null default 'view',
  score              numeric default 0,
  time_spent_seconds int,
  session_id         text,
  is_recommended     boolean default false,
  created_at         timestamptz default now()
);

alter table public.interactions enable row level security;
create policy "interactions_select_own" on public.interactions
  for select using (auth.uid() = user_id);
create policy "interactions_insert_own" on public.interactions
  for insert with check (auth.uid() = user_id);
