begin;

-- Ridge persistence for strava.runs.
--
-- PR 29 shipped the ridge card but no column, so a run saved to the hosted database lost its
-- ridge and fell back to the legacy rhythm trace on reload. These five columns are exactly the
-- five fields the Save preview already builds and sends (site/index.html line 1718) and exactly
-- the five fields the card renderer reads back by name (site/run-contract.js, function ridge).
--
-- Shapes come from the contract, not from a guess:
--   ridge              40 to 60 non-negative whole numbers   (agentgrinder/contract.py line 32)
--   worker_bins        the same length as ridge              (agentgrinder/contract.py line 36)
--   commit_bins        ridge bin indexes, may be empty       (agentgrinder/contract.py line 40)
--   ridge_basis        wall-time or call-index               (agentgrinder/contract.py line 44)
--   ridge_wall_seconds a finite non-negative number          (agentgrinder/contract.py line 47)
--
-- ridge_wall_seconds is double precision, not integer. agentgrinder/cursor_tree.py line 237
-- returns round(seconds, 1), a float, and the browser forwards that value unchanged.
--
-- All five are nullable. There is no backfill. A run saved before this migration keeps a null
-- ridge and keeps drawing its rhythm trace.
--
-- No policy or grant change. Row level security on strava.runs is row level, so every policy
-- from 002_close_friends.sql covers these columns the moment they exist. select on
-- strava.runs is already granted to anon and authenticated at table level. A close friends
-- run that an excluded reader cannot read returns no row at all, so it returns no ridge.

alter table strava.runs
  add column if not exists ridge jsonb,
  add column if not exists worker_bins jsonb,
  add column if not exists commit_bins jsonb,
  add column if not exists ridge_basis text,
  add column if not exists ridge_wall_seconds double precision;

-- The database refuses a ridge shape the card renderer would silently drop.
alter table strava.runs drop constraint if exists runs_ridge_shape_check;
alter table strava.runs
  add constraint runs_ridge_shape_check
  check (
    ridge is null
    or (
      jsonb_typeof(ridge) = 'array'
      and jsonb_array_length(ridge) between 40 and 60
      and worker_bins is not null
      and jsonb_typeof(worker_bins) = 'array'
      and jsonb_array_length(worker_bins) = jsonb_array_length(ridge)
      and (commit_bins is null or jsonb_typeof(commit_bins) = 'array')
    )
  );

alter table strava.runs drop constraint if exists runs_ridge_basis_check;
alter table strava.runs
  add constraint runs_ridge_basis_check
  check (ridge_basis is null or ridge_basis in ('wall-time', 'call-index'));

alter table strava.runs drop constraint if exists runs_ridge_wall_seconds_check;
alter table strava.runs
  add constraint runs_ridge_wall_seconds_check
  check (ridge_wall_seconds is null or ridge_wall_seconds >= 0);

comment on column strava.runs.ridge is 'Tool calls per bin, 40 to 60 bins. No tool names, arguments or paths.';
comment on column strava.runs.worker_bins is 'Concurrent workers per bin, same length as ridge.';
comment on column strava.runs.commit_bins is 'Ridge bin indexes that carried a commit.';
comment on column strava.runs.ridge_basis is 'wall-time when every call had a timestamp, otherwise call-index.';
comment on column strava.runs.ridge_wall_seconds is 'Seconds between the first and last recorded call, one decimal.';

commit;
