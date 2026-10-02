-- Private early-alpha feedback inbox. Clients may submit, never enumerate or change it.
-- App schema only; no Auth triggers, mail delivery or public-schema writes.
begin;
create table if not exists strava.alpha_feedback (
 id uuid primary key default gen_random_uuid(),
 profile_id uuid not null references strava.profiles(id) on delete cascade,
 created_at timestamptz not null default clock_timestamp(),
 category text not null check(category in ('bug','idea','other')),
 message text not null check(char_length(message) between 1 and 2000),
 page text not null default '/' check(char_length(page) between 1 and 200
  and page ~ '^/[^?#[:space:]]*$' and page !~ '^//'
  and position('://' in page)=0 and position(chr(92) in page)=0)
);
create index if not exists alpha_feedback_profile_time on strava.alpha_feedback(profile_id,created_at desc);
alter table strava.alpha_feedback enable row level security;
revoke all on strava.alpha_feedback from public,anon,authenticated;
grant insert(profile_id,category,message,page) on strava.alpha_feedback to authenticated;
drop policy if exists alpha_feedback_submit on strava.alpha_feedback;
create policy alpha_feedback_submit on strava.alpha_feedback for insert to authenticated
 with check(profile_id=strava.grinder_profile_id());

create or replace function strava.alpha_feedback_guard() returns trigger
language plpgsql security definer set search_path=strava,pg_temp as $$
begin
 if new.profile_id is distinct from strava.grinder_profile_id() or new.profile_id is null then
  raise exception 'Sign in to send feedback from your account.' using errcode='42501';
 end if;
 -- Lock first, then count, so simultaneous submissions from one account serialize.
 perform 1 from strava.profiles where id=new.profile_id for update;
 new.created_at:=clock_timestamp();
 new.message:=regexp_replace(new.message,'^[[:space:]]+|[[:space:]]+$','','g');
 if new.message is null or char_length(new.message) not between 1 and 2000 then
  raise exception 'Write feedback between 1 and 2000 characters.' using errcode='23514';
 end if;
 if (select count(*) from strava.alpha_feedback where profile_id=new.profile_id
      and created_at>new.created_at-interval '1 hour')>=5 then
  raise exception 'You have sent five messages this hour. Please try again later.' using errcode='P0001';
 end if;
 return new;
end $$;
revoke all on function strava.alpha_feedback_guard() from public,anon,authenticated;
drop trigger if exists alpha_feedback_guard on strava.alpha_feedback;
create trigger alpha_feedback_guard before insert on strava.alpha_feedback
 for each row execute function strava.alpha_feedback_guard();
commit;
