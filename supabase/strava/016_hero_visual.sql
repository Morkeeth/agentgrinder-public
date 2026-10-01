-- One evidence-backed signature visual per run. The browser only offers a choice when the
-- corresponding captured fields exist; the database keeps the preference, not generated data.
begin;

alter table strava.runs
  add column if not exists hero_visual text
  check (hero_visual is null or hero_visual in ('proof_route','activity_terrain','change_atlas','result'));

grant select (hero_visual) on strava.runs to anon, authenticated;
grant update (hero_visual) on strava.runs to authenticated;

commit;
