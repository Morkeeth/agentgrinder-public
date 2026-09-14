-- Strava identity columns: a chosen handle, display name and avatar that belong to the
-- Strava profile, not to any sign-in provider. Applied only inside the strava schema.
-- Retry-safe. Every target is qualified with strava; nothing touches Grinder.
--
-- github_handle keeps its legacy meaning (set only from a real GitHub identity) and its
-- unique key. Public lookups resolve the chosen handle first, then the legacy github_handle,
-- and the guard trigger below refuses a chosen handle that collides with either column on
-- another profile, so a URL can never quietly change owner.

alter table strava.profiles
  add column if not exists handle text,
  add column if not exists display_name text,
  add column if not exists avatar_url text;

alter table strava.profiles
  drop constraint if exists profiles_handle_format,
  add constraint profiles_handle_format
    check (handle is null or handle ~ '^[a-z0-9]([a-z0-9_-]{0,38}[a-z0-9])?$'),
  drop constraint if exists profiles_display_name_length,
  add constraint profiles_display_name_length
    check (display_name is null or length(trim(display_name)) between 1 and 60),
  drop constraint if exists profiles_avatar_url_format,
  add constraint profiles_avatar_url_format
    check (avatar_url is null or (length(avatar_url) <= 2048 and avatar_url ~ '^https://[^[:space:]]+$'));

create unique index if not exists profiles_handle_unique on strava.profiles (handle) where handle is not null;

comment on column strava.profiles.handle is
  'Chosen public handle, lowercase; never inferred to prove ownership of any external account';
comment on column strava.profiles.display_name is 'Chosen display name; falls back to legacy name';
comment on column strava.profiles.avatar_url is 'https avatar chosen by the owner; may copy a provider avatar';

-- Normalise and refuse collisions across both handle columns. Raises unique_violation so
-- clients handle it exactly like the unique index (SQLSTATE 23505).
create or replace function strava.strava_profile_handle_guard() returns trigger
language plpgsql security definer set search_path = strava, pg_temp as $$
begin
  if new.handle is not null then
    new.handle := lower(trim(new.handle));
    if new.handle = '' then new.handle := null; end if;
  end if;
  if new.display_name is not null then
    new.display_name := trim(new.display_name);
    if new.display_name = '' then new.display_name := null; end if;
  end if;
  if new.handle is not null and exists (
    select 1 from strava.profiles p
    where p.id <> new.id
      and (p.handle = new.handle or lower(p.github_handle) = new.handle)
  ) then
    raise exception 'handle_taken' using errcode = 'unique_violation';
  end if;
  if new.github_handle is not null and exists (
    select 1 from strava.profiles p
    where p.id <> new.id and p.handle = lower(new.github_handle)
  ) then
    raise exception 'handle_taken' using errcode = 'unique_violation';
  end if;
  return new;
end $$;
revoke all on function strava.strava_profile_handle_guard() from public, anon, authenticated;

drop trigger if exists strava_profile_handle_guard on strava.profiles;
create trigger strava_profile_handle_guard
  before insert or update of handle, github_handle, display_name on strava.profiles
  for each row execute function strava.strava_profile_handle_guard();

-- Public lookup used by /?u=<handle>. Chosen handle wins; legacy github_handle is the fallback.
-- security invoker: the caller's own read policy applies.
create or replace function strava.strava_profile_by_handle(lookup text)
returns setof strava.profiles
language sql stable security invoker set search_path = strava, pg_temp as $$
  select * from strava.profiles where handle = lower(trim(lookup))
  union all
  select * from strava.profiles p
  where lower(p.github_handle) = lower(trim(lookup))
    and not exists (select 1 from strava.profiles q where q.handle = lower(trim(lookup)))
  limit 1
$$;
revoke all on function strava.strava_profile_by_handle(text) from public;
grant execute on function strava.strava_profile_by_handle(text) to anon, authenticated;
