-- Photo metadata follows the parent's live audience; no separate sharing switch.
begin;
create table if not exists strava.run_photos (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references strava.runs(id) on delete cascade,
 created_at timestamptz not null default now(),
 width integer not null check(width between 1 and 2048),
 height integer not null check(height between 1 and 2048),
 byte_size integer not null check(byte_size between 1 and 3145728)
);
alter table strava.run_photos enable row level security;
revoke all on strava.run_photos from public,anon,authenticated;
grant select on strava.run_photos to anon,authenticated;
grant insert,delete on strava.run_photos to authenticated;
drop policy if exists run_photos_read on strava.run_photos;
create policy run_photos_read on strava.run_photos for select to anon,authenticated
 using(strava.grinder_can_read_run(run_id));
drop policy if exists run_photos_add on strava.run_photos;
create policy run_photos_add on strava.run_photos for insert to authenticated
 with check(exists(select 1 from strava.runs r where r.id=run_id and r.profile_id=strava.grinder_profile_id()
   and r.measurement_revision is not null and r.trace_basis is distinct from 'typed-by-author'));
drop policy if exists run_photos_remove on strava.run_photos;
create policy run_photos_remove on strava.run_photos for delete to authenticated
 using(exists(select 1 from strava.runs r where r.id=run_id and r.profile_id=strava.grinder_profile_id()));

create or replace function strava.run_photo_limit() returns trigger
language plpgsql security definer set search_path=strava,pg_temp as $$
begin
 perform 1 from strava.runs where id=new.run_id for update;
 if (select count(*) from strava.run_photos where run_id=new.run_id)>=6 then
  raise exception 'A run can have up to six photos. Remove one before adding another.';
 end if;
 return new;
end $$;
revoke all on function strava.run_photo_limit() from public,anon,authenticated;
drop trigger if exists run_photo_limit on strava.run_photos;
create trigger run_photo_limit before insert on strava.run_photos for each row execute function strava.run_photo_limit();

-- Cascading run/account deletion must not lose the object-erasure obligation.
-- No client can inspect or inject queue entries. A server maintenance helper drains it.
create table if not exists strava.photo_deletion_queue (
 object_name text primary key,
 requested_at timestamptz not null default now()
);
alter table strava.photo_deletion_queue enable row level security;
revoke all on strava.photo_deletion_queue from public,anon,authenticated;
do $$ begin
 if exists(select 1 from pg_roles where rolname='service_role') then
  grant usage on schema strava to service_role;
  grant select,delete on strava.photo_deletion_queue to service_role;
 end if;
end $$;
create or replace function strava.queue_run_photo_deletion() returns trigger
language plpgsql security definer set search_path=strava,pg_temp as $$
begin
 insert into strava.photo_deletion_queue(object_name) values(old.run_id::text||'/'||old.id::text||'.jpg') on conflict do nothing;
 return old;
end $$;
revoke all on function strava.queue_run_photo_deletion() from public,anon,authenticated;
drop trigger if exists queue_run_photo_deletion on strava.run_photos;
create trigger queue_run_photo_deletion after delete on strava.run_photos for each row execute function strava.queue_run_photo_deletion();

commit;
