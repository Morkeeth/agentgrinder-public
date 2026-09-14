-- Friend lookup for ordinary follows. Identity columns (handle, display_name, avatar_url)
-- are owned by a separate migration; this searches github_handle and name only.
-- Applied inside the strava schema by prepare-strava-database.py. Never touches public.
begin;

create or replace function public.grinder_escape_like(raw text) returns text
language sql immutable set search_path = public as $$
  select replace(replace(replace(coalesce(raw, ''), '\', '\\'), '%', '\%'), '_', '\_')
$$;

-- Returns a JSON array so PostgREST and the disposable shim both expose every match.
create or replace function public.grinder_find_people(q text, lim integer default 20)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with needle as (
    select trim(coalesce(q, '')) as q,
           least(greatest(coalesce(lim, 20), 1), 50) as lim
  ),
  me as (
    select public.grinder_profile_id() as id
  ),
  matched as (
    select p.id, p.github_handle, p.name, p.created_at
    from public.profiles p
    cross join needle n
    cross join me
    where length(n.q) >= 1
      and p.github_handle is not null
      and length(trim(p.github_handle)) > 0
      and (
        p.github_handle ilike '%' || public.grinder_escape_like(n.q) || '%' escape '\'
        or coalesce(p.name, '') ilike '%' || public.grinder_escape_like(n.q) || '%' escape '\'
      )
      and (me.id is null or not public.grinder_blocked_pair(p.id, me.id))
    order by
      case
        when lower(p.github_handle) = lower(n.q) then 0
        when lower(p.github_handle) like lower(public.grinder_escape_like(n.q)) || '%' escape '\' then 1
        when lower(coalesce(p.name, '')) = lower(n.q) then 2
        else 3
      end,
      p.created_at desc
    limit (select lim from needle)
  )
  select coalesce(jsonb_agg(to_jsonb(matched)), '[]'::jsonb) from matched;
$$;

revoke all on function public.grinder_escape_like(text) from public, anon, authenticated;
revoke all on function public.grinder_find_people(text, integer) from public;
grant execute on function public.grinder_find_people(text, integer) to anon, authenticated;

create or replace function public.grinder_recent_builders(lim integer default 12)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with me as (select public.grinder_profile_id() as id),
  builders as (
    select p.id,
           p.github_handle,
           p.name,
           count(r.id) as public_runs,
           max(r.created_at) as last_public_at
    from public.profiles p
    join public.runs r on r.profile_id = p.id and r.visibility = 'public'
    cross join me
    where p.github_handle is not null
      and length(trim(p.github_handle)) > 0
      and (me.id is null or p.id is distinct from me.id)
      and (me.id is null or not public.grinder_blocked_pair(p.id, me.id))
    group by p.id, p.github_handle, p.name
    order by max(r.created_at) desc
    limit least(greatest(coalesce(lim, 12), 1), 40)
  )
  select coalesce(jsonb_agg(to_jsonb(builders)), '[]'::jsonb) from builders;
$$;

revoke all on function public.grinder_recent_builders(integer) from public;
grant execute on function public.grinder_recent_builders(integer) to anon, authenticated;

commit;
