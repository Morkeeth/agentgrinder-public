-- Reverse of supabase/strava/011_connect_device.sql.
--
-- Down migrations live in this folder so the first-install bootstrap
-- (scripts/prepare-strava-database.py, which globs supabase/strava/*.sql) never applies one.
-- After this script the schema is what 010 left behind: no pairings, no funnel, no device token
-- renewal, and agent_token_create / agent_token_list exactly as 007 defines them.
--
-- Pairings and funnel rows are dropped with their tables. They hold no content, only step names
-- and times, and a device that was paired keeps working until its token expires or is revoked.

begin;

drop trigger if exists connect_token_touch on strava.grinder_agent_requests;

drop function if exists strava.connect_token_touch();
drop function if exists strava.connect_device_poll(text);
drop function if exists strava.connect_device_start(text,text,text[]);
drop function if exists strava.connect_pairing_decide(text,boolean);
drop function if exists strava.connect_pairing_view(text);
drop function if exists strava.connect_sweep_expired();
drop function if exists strava.connect_funnel_note(uuid,text);
drop function if exists strava.connect_user_code();

drop table if exists strava.connect_funnel_events;
drop table if exists strava.connect_pairings;

drop function if exists strava.connect_code_hash(text);

alter table strava.grinder_agent_tokens drop column if exists last_seen_at;

-- 007 definitions, restored verbatim.
create or replace function strava.agent_token_create(p_label text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare me uuid:=strava.grinder_profile_id(); clean text:=trim(p_label); connect_agent uuid; issued jsonb; minted strava.grinder_agent_tokens;
begin
 if me is null then raise exception 'Sign in to connect an agent'; end if;
 if clean is null or length(clean) not between 1 and 80 then raise exception 'A label is 1 to 80 characters'; end if;
 -- Serialise per profile so two clicks cannot pass the cap together.
 perform 1 from strava.profiles where id=me for update;
 if (select count(*) from strava.grinder_agent_tokens t join strava.grinder_agents a on a.id=t.agent_id
     where a.owner_id=me and t.label is not null and not t.revoked and t.expires_at>now())>=5 then
  raise exception 'Revoke a connected agent before adding another (five active)';
 end if;
 select id into connect_agent from strava.grinder_agents where owner_id=me and name='Connect' order by created_at limit 1;
 if connect_agent is null then
  insert into strava.grinder_agents(owner_id,name,visibility) values(me,'Connect','private') returning id into connect_agent;
 end if;
 issued=strava.grinder_issue_agent_token(connect_agent,array['draft','publish'],array['private'],now()+interval '30 days');
 update strava.grinder_agent_tokens set label=clean,token_prefix=left(issued->>'token',8)
  where id=(issued->>'id')::uuid returning * into minted;
 return jsonb_build_object('id',minted.id,'label',minted.label,'token',issued->>'token','token_prefix',minted.token_prefix,
  'created_at',minted.created_at,'expires_at',minted.expires_at,'scopes',to_jsonb(minted.scopes),'audiences',to_jsonb(minted.audiences));
end $function$;

create or replace function strava.agent_token_list()
 returns jsonb
 language sql
 stable
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
 select coalesce(jsonb_agg(jsonb_build_object('id',t.id,'label',t.label,'token_prefix',t.token_prefix,'created_at',t.created_at,
   'expires_at',t.expires_at,'revoked',t.revoked,'scopes',to_jsonb(t.scopes),'audiences',to_jsonb(t.audiences)) order by t.created_at desc),'[]'::jsonb)
 from strava.grinder_agent_tokens t join strava.grinder_agents a on a.id=t.agent_id
 where a.owner_id=strava.grinder_profile_id() and t.label is not null
$function$;

commit;
