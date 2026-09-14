# Night release integration

Review fixes are integrated: dedup uses measurement_revision only, never start time plus harness; schema-zero revisions persist; a partial unique index arbitrates concurrent measured captures. Legacy captures without a revision are not claimed idempotent.

Deployment prerequisite: inspect duplicates grouped by profile_id and measurement_revision in strava.runs, excluding NULL revisions. If any exist, stop and preserve every row for a reviewed reconciliation; do not delete data to force the index. Apply supabase/strava/run_capture_unique.sql only after explicit deployment/database authority is confirmed. No public/Grinder schema changes. No migration or production deployment performed in this night run.

Root conflict resolution kept the reviewer disclosure and the author's stack-notes detail. Lost-response browser check now uses a valid stable measurement revision. Final check-post-recovery.py: 29 passed, zero failed, no JS errors; nine focused pytest checks pass. This is local disposable TEST DATA, not hosted OAuth or real-user acceptance.
