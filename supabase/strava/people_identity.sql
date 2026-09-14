-- Provider-neutral people discovery. Applied after identity.sql; Strava only.
begin;
create or replace function strava.grinder_find_people(q text, lim integer default 20)
returns jsonb language sql stable security definer set search_path=strava,pg_temp as $$
  with needle as (
    select trim(coalesce(q,'')) as q, least(greatest(coalesce(lim,20),1),50) as lim
  ), me as (select strava.grinder_profile_id() as id),
  people as (
    select p.id,p.github_handle,p.name,p.created_at,
           coalesce(nullif(p.handle,''),nullif(p.github_handle,'')) as handle,
           coalesce(nullif(p.display_name,''),nullif(p.name,''),
                    '@'||coalesce(p.handle,p.github_handle)) as display_name,
           p.avatar_url
    from strava.profiles p
  ), matched as (
    select p.* from people p cross join needle n cross join me
    where length(n.q)>0 and p.handle is not null
      and (p.handle ilike '%'||strava.grinder_escape_like(n.q)||'%' escape '\'
        or p.github_handle ilike '%'||strava.grinder_escape_like(n.q)||'%' escape '\'
        or p.display_name ilike '%'||strava.grinder_escape_like(n.q)||'%' escape '\'
        or p.name ilike '%'||strava.grinder_escape_like(n.q)||'%' escape '\')
      and (me.id is null or not strava.grinder_blocked_pair(p.id,me.id))
    order by case when lower(p.handle)=lower(n.q) then 0
      when lower(p.handle) like lower(strava.grinder_escape_like(n.q))||'%' escape '\' then 1
      when lower(p.display_name)=lower(n.q) then 2 else 3 end,
      p.created_at desc,p.id
    limit (select lim from needle)
  ) select coalesce(jsonb_agg(to_jsonb(matched)),'[]'::jsonb) from matched;
$$;
revoke all on function strava.grinder_find_people(text,integer) from public,anon,authenticated;
grant execute on function strava.grinder_find_people(text,integer) to anon,authenticated;

create or replace function strava.grinder_recent_builders(lim integer default 12)
returns jsonb language sql stable security definer set search_path=strava,pg_temp as $$
  with me as (select strava.grinder_profile_id() as id), builders as (
    select p.id,p.github_handle,p.name,
           coalesce(nullif(p.handle,''),nullif(p.github_handle,'')) as handle,
           coalesce(nullif(p.display_name,''),nullif(p.name,''),
                    '@'||coalesce(p.handle,p.github_handle)) as display_name,
           p.avatar_url,count(r.id) as public_runs,max(r.created_at) as last_public_at
    from strava.profiles p
    join strava.runs r on r.profile_id=p.id and r.visibility='public'
    cross join me
    where coalesce(nullif(p.handle,''),nullif(p.github_handle,'')) is not null
      and (me.id is null or p.id<>me.id)
      and (me.id is null or not strava.grinder_blocked_pair(p.id,me.id))
    group by p.id
    order by max(r.created_at) desc,p.id
    limit least(greatest(coalesce(lim,12),1),40)
  ) select coalesce(jsonb_agg(to_jsonb(builders)),'[]'::jsonb) from builders;
$$;
revoke all on function strava.grinder_recent_builders(integer) from public,anon,authenticated;
grant execute on function strava.grinder_recent_builders(integer) to anon,authenticated;
commit;
