-- THE X HANDLE ON A PROFILE. A profile already carries github_handle, written only from a real
-- GitHub identity on the signed-in Auth user (site/auth.js syncGithubHandle). This adds the same
-- for X: x_handle, written only from an X identity (provider x, or the legacy twitter) that
-- Supabase Auth reports on the user. A chosen handle never becomes an x_handle.
--
-- Additive. One optional column, one check, one unique index. No policy, grant, function or
-- trigger changes: the profiles table already carries table-level SELECT for anon and
-- authenticated, and owner-only INSERT/UPDATE for authenticated, so the new column is readable
-- by everyone and writable by its owner exactly as github_handle is.
--
-- The check is X's own rule: 1 to 15 characters, letters, digits and underscore.
begin;

alter table strava.profiles add column if not exists x_handle text
  check (x_handle is null or x_handle ~ '^[A-Za-z0-9_]{1,15}$');

create unique index if not exists profiles_x_handle_key
  on strava.profiles (lower(x_handle)) where x_handle is not null;

commit;
