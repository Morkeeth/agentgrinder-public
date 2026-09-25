-- THE SOCIAL PRODUCT, 25 Sep 2026 evening (Oscar: "follow friends, build a profile, and see the
-- feed, the clubs, the events happening"). Three additive pieces. Nothing that exists changes.
--
-- 1. A profile carries a short bio and the agents its owner uses. Both optional, both checked
--    here. The profiles table already grants SELECT to anon and authenticated and owner-only
--    INSERT/UPDATE to authenticated, so the new columns are readable by all and writable by
--    their owner exactly as display_name is.
-- 2. Clubs are the existing Crews. A public Club can now be joined without an invitation, by
--    the signed-in person, for themselves only. Leaving stays grinder_remove_member.
-- 3. Events: a Club owner posts an event (title, time, place or link); signed-in people join or
--    leave it. Readable when the Club is public or the reader is a member. Rows are only
--    written through the functions below; clients have no direct write.
begin;

-- 1. Profile
alter table strava.profiles add column if not exists bio text
  check (bio is null or char_length(bio) <= 160);
alter table strava.profiles add column if not exists agents text[]
  check (agents is null or (cardinality(agents) <= 8
    and agents <@ array['claude-code','cursor','codex','grok','gemini','copilot','other']::text[]));

-- 2. Join a public Club
create or replace function strava.grinder_join_public_crew(crew uuid)
returns uuid language plpgsql security definer set search_path = strava, pg_temp as $$
declare me uuid := grinder_profile_id();
begin
  if me is null then raise exception 'Sign in to join a Club'; end if;
  if not exists(select 1 from grinder_crews where id = crew and visibility = 'public') then
    raise exception 'This Club is private or unavailable';
  end if;
  insert into grinder_memberships(crew_id, profile_id, role) values (crew, me, 'member') on conflict do nothing;
  return crew;
end $$;
revoke all on function strava.grinder_join_public_crew(uuid) from public, anon;
grant execute on function strava.grinder_join_public_crew(uuid) to authenticated;

-- 3. Events
create table if not exists strava.grinder_events (
  id uuid primary key default gen_random_uuid(),
  crew_id uuid not null references strava.grinder_crews(id) on delete cascade,
  owner_id uuid not null references strava.profiles(id) on delete cascade,
  title text not null check (char_length(trim(title)) between 1 and 120),
  about text not null default '' check (char_length(about) <= 1000),
  place text not null default '' check (char_length(place) <= 200),
  starts_at timestamptz not null,
  created_at timestamptz not null default now()
);
create index if not exists grinder_events_starts on strava.grinder_events (starts_at);
create table if not exists strava.grinder_event_people (
  event_id uuid not null references strava.grinder_events(id) on delete cascade,
  profile_id uuid not null references strava.profiles(id) on delete cascade,
  joined_at timestamptz not null default now(),
  primary key (event_id, profile_id)
);
alter table strava.grinder_events enable row level security;
alter table strava.grinder_event_people enable row level security;
revoke all on strava.grinder_events, strava.grinder_event_people from public, anon, authenticated;
grant select on strava.grinder_events, strava.grinder_event_people to anon, authenticated;

drop policy if exists grinder_events_read on strava.grinder_events;
create policy grinder_events_read on strava.grinder_events for select using (
  exists(select 1 from strava.grinder_crews c where c.id = crew_id and c.visibility = 'public')
  or strava.grinder_is_member(crew_id));
drop policy if exists grinder_event_people_read on strava.grinder_event_people;
create policy grinder_event_people_read on strava.grinder_event_people for select using (
  exists(select 1 from strava.grinder_events e join strava.grinder_crews c on c.id = e.crew_id
         where e.id = event_id and (c.visibility = 'public' or strava.grinder_is_member(c.id))));

create or replace function strava.grinder_create_event(club uuid, event_title text, event_about text, event_place text, starts timestamptz)
returns uuid language plpgsql security definer set search_path = strava, pg_temp as $$
declare me uuid := grinder_profile_id(); result uuid;
begin
  if me is null then raise exception 'Sign in to post an event'; end if;
  if not grinder_owns_crew(club) then raise exception 'Only the Club owner can post an event'; end if;
  if starts is null or starts <= now() then raise exception 'Choose a start time in the future'; end if;
  insert into grinder_events(crew_id, owner_id, title, about, place, starts_at)
  values (club, me, trim(event_title), coalesce(event_about, ''), coalesce(event_place, ''), starts) returning id into result;
  insert into grinder_event_people(event_id, profile_id) values (result, me) on conflict do nothing;
  return result;
end $$;

create or replace function strava.grinder_join_event(event uuid)
returns void language plpgsql security definer set search_path = strava, pg_temp as $$
declare me uuid := grinder_profile_id(); club uuid;
begin
  if me is null then raise exception 'Sign in to join an event'; end if;
  select e.crew_id into club from grinder_events e join grinder_crews c on c.id = e.crew_id
   where e.id = event and (c.visibility = 'public' or grinder_is_member(c.id)) and e.starts_at > now();
  if club is null then raise exception 'This event is private, over or unavailable'; end if;
  insert into grinder_event_people(event_id, profile_id) values (event, me) on conflict do nothing;
end $$;

create or replace function strava.grinder_leave_event(event uuid)
returns void language plpgsql security definer set search_path = strava, pg_temp as $$
declare me uuid := grinder_profile_id();
begin
  if me is null then raise exception 'Sign in first'; end if;
  delete from grinder_event_people where event_id = event and profile_id = me;
end $$;

create or replace function strava.grinder_delete_event(event uuid)
returns void language plpgsql security definer set search_path = strava, pg_temp as $$
begin
  if not exists(select 1 from grinder_events where id = event and owner_id = grinder_profile_id()) then
    raise exception 'Only the host can remove this event';
  end if;
  delete from grinder_events where id = event;
end $$;

revoke all on function strava.grinder_create_event(uuid, text, text, text, timestamptz) from public, anon;
revoke all on function strava.grinder_join_event(uuid) from public, anon;
revoke all on function strava.grinder_leave_event(uuid) from public, anon;
revoke all on function strava.grinder_delete_event(uuid) from public, anon;
grant execute on function strava.grinder_create_event(uuid, text, text, text, timestamptz) to authenticated;
grant execute on function strava.grinder_join_event(uuid) to authenticated;
grant execute on function strava.grinder_leave_event(uuid) to authenticated;
grant execute on function strava.grinder_delete_event(uuid) to authenticated;

commit;
