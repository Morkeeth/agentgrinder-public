-- PIN RUNS TO A PROFILE (Oscar's product order, 25 Sep 23:1x: "Pin stuff to profile").
-- A run carries pinned_at; the profile shows pinned runs first, newest pin first. Up to 3 per
-- profile, checked here. Only the owner can set it: runs already allow UPDATE to the owner alone
-- (RLS grinder_run_update), and the column grant below is the only new write. Additive.
begin;

alter table strava.runs add column if not exists pinned_at timestamptz;
grant update (pinned_at) on strava.runs to authenticated;

create or replace function strava.grinder_pin_limit()
returns trigger language plpgsql security definer set search_path = strava, pg_temp as $$
begin
  if new.pinned_at is not null and (old.pinned_at is null or tg_op = 'INSERT') then
    -- Serialise pins per profile so two tabs cannot both take the third slot.
    perform pg_advisory_xact_lock(hashtext('grinder_pin:' || new.profile_id::text));
    if (select count(*) from runs where profile_id = new.profile_id and pinned_at is not null and id <> new.id) >= 3 then
      raise exception 'Pin up to 3 runs. Unpin one first.';
    end if;
  end if;
  return new;
end $$;

drop trigger if exists grinder_pin_limit on strava.runs;
create trigger grinder_pin_limit before insert or update of pinned_at on strava.runs
  for each row execute function strava.grinder_pin_limit();

create index if not exists runs_pinned on strava.runs (profile_id, pinned_at) where pinned_at is not null;

commit;
