-- Link audience is relationship-gated: signed-in readers on the author's close-friends
-- list must be able to prove that membership (owners already can read close_friends).
-- Followers are checked via grinder_follows from the client; this helper covers close friends.
begin;

create or replace function strava.grinder_is_close_friend_of(owner uuid)
returns boolean
language sql
stable
security definer
set search_path = strava, pg_temp
as $$
  select owner is not null
    and exists (
      select 1
      from strava.close_friends cf
      where cf.owner_profile_id = owner
        and cf.friend_profile_id = strava.grinder_profile_id()
    )
$$;

revoke all on function strava.grinder_is_close_friend_of(uuid) from public, anon, authenticated;
grant execute on function strava.grinder_is_close_friend_of(uuid) to authenticated;

commit;
