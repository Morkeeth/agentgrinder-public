-- Apply after strava/018. Server-only Storage: /api/run-photos checks parent RLS
-- and strips metadata. Never grant clients access or create signed URLs.
begin;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('strive-run-photos','strive-run-photos',false,3145728,array['image/jpeg'])
 on conflict(id) do update set public=false,file_size_limit=3145728,allowed_mime_types=array['image/jpeg'];
drop policy if exists strive_run_photos_read on storage.objects;
drop policy if exists strive_run_photos_insert on storage.objects;
drop policy if exists strive_run_photos_delete on storage.objects;
drop policy if exists strive_run_photos_server_only on storage.objects;
-- Restrictive composes with broad policies from other apps. service_role alone bypasses RLS.
create policy strive_run_photos_server_only on storage.objects as restrictive for all to anon,authenticated
 using(bucket_id<>'strive-run-photos') with check(bucket_id<>'strive-run-photos');
commit;
