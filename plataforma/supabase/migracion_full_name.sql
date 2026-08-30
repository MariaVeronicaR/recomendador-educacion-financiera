-- Migración: añadir la columna full_name a la tabla profiles
-- (ejecutar en el SQL Editor de Supabase si ya creaste el esquema antes)
alter table public.profiles
  add column if not exists full_name text;
