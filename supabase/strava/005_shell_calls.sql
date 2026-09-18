-- Renamed from 004_shell_calls.sql on 2026-09-18.
-- Two files were numbered 004 after PR 41 merged: this one and 004_ridge_turn_order.sql.
-- A runner that applies migrations in order and records the number would mark 004 done
-- and skip this file forever, with no error and no red light.
-- Applied to production on 2026-09-18 under the ledger name 005_shell_calls_from_main_004,
-- because the column was missing while main already selected it.

begin;

-- A shell call is a structured Shell tool request in a supported capture.
-- It is a count only. Command text, results, paths, and exit output are not stored.
-- Existing runs stay null because an older capture did not record this field.

alter table strava.runs
  add column if not exists shell_calls integer;

alter table strava.runs drop constraint if exists runs_shell_calls_check;
alter table strava.runs
  add constraint runs_shell_calls_check
  check (shell_calls is null or shell_calls >= 0);

comment on column strava.runs.shell_calls is
  'Structured shell tool requests. No command text, output, or paths.';

commit;
