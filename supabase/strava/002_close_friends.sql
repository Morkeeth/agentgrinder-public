begin;

create table if not exists strava.close_friends (
  owner_profile_id uuid not null references strava.profiles(id) on delete cascade,
  friend_profile_id uuid not null references strava.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (owner_profile_id, friend_profile_id),
  constraint close_friends_not_self check (owner_profile_id <> friend_profile_id)
);

alter table strava.close_friends enable row level security;

drop policy if exists close_friends_owner_read on strava.close_friends;
create policy close_friends_owner_read
  on strava.close_friends
  for select
  to authenticated
  using (owner_profile_id = strava.grinder_profile_id());

drop policy if exists close_friends_owner_add on strava.close_friends;
create policy close_friends_owner_add
  on strava.close_friends
  for insert
  to authenticated
  with check (owner_profile_id = strava.grinder_profile_id());

drop policy if exists close_friends_owner_remove on strava.close_friends;
create policy close_friends_owner_remove
  on strava.close_friends
  for delete
  to authenticated
  using (owner_profile_id = strava.grinder_profile_id());

revoke all on strava.close_friends from public, anon, authenticated;
grant select, insert, delete on strava.close_friends to authenticated;

create or replace function strava.grinder_require_close_friends_for_run()
returns trigger
language plpgsql
security definer
set search_path = strava, pg_temp
as $$
begin
  if new.visibility = 'close_friends'
    and not exists (
      select 1
      from strava.close_friends cf
      where cf.owner_profile_id = new.profile_id
    )
  then
    raise exception using
      errcode = '23514',
      message = 'Add at least one close friend before saving for Close friends.';
  end if;
  return new;
end
$$;
revoke all on function strava.grinder_require_close_friends_for_run() from public, anon, authenticated;

drop trigger if exists grinder_require_close_friends_for_run on strava.runs;
create trigger grinder_require_close_friends_for_run
  before insert or update of visibility, profile_id
  on strava.runs
  for each row
  execute function strava.grinder_require_close_friends_for_run();

create or replace function strava.grinder_close_friend_can_read_run(target uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select exists (
    select 1
    from strava.runs r
    join strava.close_friends cf
      on cf.owner_profile_id = r.profile_id
    where r.id = target
      and r.visibility = 'close_friends'
      and cf.friend_profile_id = strava.grinder_profile_id()
  )
$$;
revoke all on function strava.grinder_close_friend_can_read_run(uuid) from public, anon, authenticated;
grant execute on function strava.grinder_close_friend_can_read_run(uuid) to anon, authenticated;

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
    if not exists (
      select 1
      from strava.runs r
      where r.id = new.run_id
        and (
          r.visibility in ('public', 'link')
          or strava.grinder_close_friend_can_read_run(r.id)
          or (
            r.crew_shared
            and r.visibility <> 'close_friends'
            and exists (
              select 1
              from strava.grinder_memberships gm
              where gm.crew_id = r.crew_id
                and gm.profile_id = actor
            )
          )
        )
    ) then
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

alter table strava.runs
  drop constraint if exists runs_visibility_check;
alter table strava.runs
  add constraint runs_visibility_check
  check (visibility in ('private', 'close_friends', 'link', 'public', 'crew', 'anonymous'));

drop policy if exists grinder_close_friends_runs_read on strava.runs;
create policy grinder_close_friends_runs_read
  on strava.runs
  for select
  to authenticated
  using (
    visibility = 'close_friends'
    and strava.grinder_close_friend_can_read_run(id)
  );

-- This restrictive policy prevents any Crew or legacy link policy from widening
-- a Close friends run beyond its owner-maintained audience.
drop policy if exists grinder_close_friends_audience on strava.runs;
create policy grinder_close_friends_audience
  on strava.runs
  as restrictive
  for select
  to anon, authenticated
  using (
    visibility <> 'close_friends'
    or profile_id = strava.grinder_profile_id()
    or strava.grinder_close_friend_can_read_run(id)
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

commit;
