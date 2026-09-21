-- Link audience is relationship-gated (Oscar ruling, 21 Sep 2026).
-- Public stays world-readable. Link still requires the run-id bearer header so rows are not
-- enumerable in collection queries, AND the signed-in reader must follow the author or be on
-- their close-friends list (owners always can). The URL alone is never enough.
begin;

create or replace function strava.grinder_is_close_friend_of(owner uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select owner is not null
    and strava.grinder_profile_id() is not null
    and exists (
      select 1
      from strava.close_friends cf
      where cf.owner_profile_id = owner
        and cf.friend_profile_id = strava.grinder_profile_id()
    )
$$;

revoke all on function strava.grinder_is_close_friend_of(uuid) from public, anon, authenticated;
grant execute on function strava.grinder_is_close_friend_of(uuid) to authenticated;

create or replace function strava.grinder_follows_author(author uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select author is not null
    and strava.grinder_profile_id() is not null
    and exists (
      select 1
      from strava.grinder_follows f
      where f.follower_id = strava.grinder_profile_id()
        and f.followed_id = author
    )
$$;

revoke all on function strava.grinder_follows_author(uuid) from public, anon, authenticated;
grant execute on function strava.grinder_follows_author(uuid) to authenticated;

create or replace function strava.grinder_link_relationship(author uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select strava.grinder_follows_author(author)
      or strava.grinder_is_close_friend_of(author)
$$;

revoke all on function strava.grinder_link_relationship(uuid) from public, anon, authenticated;
-- Anon must EXECUTE this function: the restrictive runs policy calls it for every SELECT,
-- including public rows. The body still returns false when grinder_profile_id() is null.
grant execute on function strava.grinder_link_relationship(uuid) to anon, authenticated;

-- Restrictive: Link rows need the bearer header plus a relationship (or ownership / crew).
drop policy if exists grinder_link_not_enumerable on strava.runs;
create policy grinder_link_not_enumerable
  on strava.runs
  as restrictive
  for select
  to anon, authenticated
  using (
    visibility <> 'link'
    or profile_id = strava.grinder_profile_id()
    or (
      strava.grinder_link_access(id)
      and strava.grinder_link_relationship(profile_id)
    )
    or (
      crew_shared
      and strava.grinder_is_member(crew_id)
      and visibility <> 'close_friends'
    )
  );

create or replace function strava.grinder_can_read_run(target uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select exists (
    select 1
    from strava.runs r
    where r.id = target
      and not strava.grinder_blocked_pair(r.profile_id, strava.grinder_profile_id())
      and (
        r.profile_id = strava.grinder_profile_id()
        or r.visibility = 'public'
        or strava.grinder_close_friend_can_read_run(r.id)
        or (
          r.visibility = 'link'
          and strava.grinder_link_access(r.id)
          and strava.grinder_link_relationship(r.profile_id)
        )
        or (
          r.crew_shared
          and strava.grinder_is_member(r.crew_id)
          and r.visibility <> 'close_friends'
        )
      )
  )
$$;

revoke all on function strava.grinder_can_read_run(uuid) from public;
grant execute on function strava.grinder_can_read_run(uuid) to anon, authenticated;

-- ACKs and replies on Link runs must use the same relationship gate as reads.
create or replace function strava.grinder_interaction_guard()
returns trigger
language plpgsql
security definer
set search_path = strava, pg_temp
as $$
declare actor uuid; target uuid;
begin
  if tg_table_name = 'grinder_replies' then
    actor := new.author_id;
    select r.profile_id into target
    from strava.runs r
    where r.id = new.run_id;
  elsif tg_table_name = 'acks' then
    actor := new.from_profile;
    select r.profile_id into target
    from strava.runs r
    where r.id = new.run_id;
    if target is null or target = new.from_profile or target is distinct from new.to_profile then
      raise exception 'ACK needs another owner and their grind';
    end if;
    if new.reason is null or new.reason <> all(array['shipped','focus','pace','rig','comeback','handoff']) then
      raise exception 'Choose a supported ACK reason';
    end if;
    if not strava.grinder_can_read_run(new.run_id) then
      raise exception 'Grind unavailable';
    end if;
  else
    actor := new.follower_id;
    target := new.followed_id;
  end if;
  if strava.grinder_blocked_pair(actor, target) then
    raise exception 'This interaction is unavailable';
  end if;
  return new;
end
$$;
revoke all on function strava.grinder_interaction_guard() from public, anon, authenticated;

commit;
