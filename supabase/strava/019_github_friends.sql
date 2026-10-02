-- Match public STRIVE identities against GitHub numeric IDs. Never expose Auth rows.
begin;
create or replace function strava.strava_github_matches(github_ids text[])
returns jsonb language plpgsql stable security definer set search_path=strava,pg_temp as $$
declare me uuid := strava.grinder_profile_id(); answer jsonb;
begin
 if auth.uid() is null or me is null then raise exception 'Sign in required' using errcode='42501'; end if;
 if coalesce(cardinality(github_ids),0)>500 then raise exception 'Too many identities'; end if;
 select coalesce(jsonb_agg(row_to_json(m)), '[]'::jsonb) into answer from (
  select distinct p.id,p.handle,p.display_name,p.avatar_url,p.github_handle
  from strava.profiles p join auth.identities i on i.user_id=p.auth_uid
  where i.provider='github' and i.identity_data->>'sub' ~ '^[0-9]+$'
   and i.identity_data->>'sub'=any(github_ids)
   and p.id<>me and not strava.grinder_blocked_pair(p.id,me)
   and coalesce(p.handle,p.github_handle) is not null
 ) m;
 return answer;
end $$;
revoke all on function strava.strava_github_matches(text[]) from public,anon;
grant execute on function strava.strava_github_matches(text[]) to authenticated;
commit;
