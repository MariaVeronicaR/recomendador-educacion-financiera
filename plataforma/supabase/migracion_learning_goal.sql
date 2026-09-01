-- Migración: añadir la columna learning_goal a la tabla profiles
-- (ejecutar en el SQL Editor de Supabase si ya creaste el esquema antes)
alter table public.profiles
  add column if not exists learning_goal text;
