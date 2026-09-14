-- One measured capture per profile. Client lookup-before-insert is not enough under
-- concurrent or lost-response retries; the unique index is the arbitration.
-- Strava schema only. Never touches public/Grinder.
begin;

create unique index if not exists runs_profile_measurement_revision_unique
  on strava.runs (profile_id, measurement_revision)
  where measurement_revision is not null;

comment on index strava.runs_profile_measurement_revision_unique is
  'Same measurement revision cannot create two runs for one profile';

commit;
