-- Migración: añadir la columna big_three a la tabla profiles
-- (ejecutar en el SQL Editor de Supabase si ya creaste el esquema antes)
alter table public.profiles
  add column if not exists big_three jsonb default '[]'::jsonb;
