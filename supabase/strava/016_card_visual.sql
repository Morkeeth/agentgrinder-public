-- One author-selected proof visual per run. The card can show a real output image, the captured
-- work route, or the recorded run rhythm. Missing data does not become a decorative fallback.
begin;

alter table strava.runs add column if not exists visual_choice text
  check (visual_choice is null or visual_choice in ('image','route','activity'));

grant select (visual_choice) on strava.runs to anon, authenticated;
grant insert (visual_choice), update (visual_choice) on strava.runs to authenticated;

commit;
