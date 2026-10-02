-- A typed social username does not establish ownership of an external identity.
-- Preserve historical labels; the UI must not call those verified accounts.
begin;
create or replace function strava.strava_x_identity_guard() returns trigger
language plpgsql security definer set search_path=strava,pg_temp as $$
begin
 if new.x_handle is not null and (tg_op='INSERT' or new.x_handle is distinct from old.x_handle
   or new.auth_uid is distinct from old.auth_uid) then
  if not exists (
   select 1 from auth.identities i
   where i.user_id=auth.uid() and i.user_id=new.auth_uid and i.provider in ('x','twitter')
    and lower(coalesce(nullif(i.identity_data->>'user_name',''),
      nullif(i.identity_data->>'preferred_username',''),
      nullif(i.identity_data->>'screen_name',''),nullif(i.identity_data->>'username','')))=lower(new.x_handle)
  ) then raise exception 'Connect your X account before adding its username.' using errcode='42501'; end if;
 end if;
 return new;
end $$;
revoke all on function strava.strava_x_identity_guard() from public,anon,authenticated;
drop trigger if exists strava_x_identity_guard on strava.profiles;
create trigger strava_x_identity_guard before insert or update of x_handle,auth_uid on strava.profiles
 for each row execute function strava.strava_x_identity_guard();
commit;
