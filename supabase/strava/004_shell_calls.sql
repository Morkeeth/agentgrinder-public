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
