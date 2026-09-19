-- 007: Connect tokens for STRIVE. One click in site/ gives the owner a private upload token.
--
-- Thin wrappers over the deployed facility, read 2026-09-19: strava.grinder_agents,
-- strava.grinder_agent_tokens and strava.grinder_issue_agent_token. No second token table.
-- The issuer still mints the secret, stores only its sha256 hash and enforces its own rules.
--
-- Defaults, owner-private: scopes draft and publish, audience private only, 30 day expiry,
-- five active Connect tokens per profile. Widening the audience stays with the existing
-- per-agent grant form in site/social.js.

begin;

-- The label marks a Connect token. Only agent_token_create sets it, and owners hold no UPDATE
-- grant on it (they may update revoked only), so list and cap key on it. They never key on the
-- agent name, which owners can rename.
-- The label is the owner's own text. The prefix is the first 8 characters of the
-- secret ("ag_" plus 5 hex digits), too short to help guess a 244-bit token.
alter table strava.grinder_agent_tokens add column if not exists label text;
alter table strava.grinder_agent_tokens add column if not exists token_prefix text;
do $$ begin
 if not exists(select 1 from pg_constraint where conname='grinder_agent_tokens_label_check') then
  alter table strava.grinder_agent_tokens add constraint grinder_agent_tokens_label_check
   check(label is null or length(label) between 1 and 80);
 end if;
end $$;

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

create or replace function strava.agent_token_revoke(p_id uuid)
 returns boolean
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
begin
 update strava.grinder_agent_tokens t set revoked=true
  from strava.grinder_agents a
  where t.id=p_id and a.id=t.agent_id and a.owner_id=strava.grinder_profile_id();
 if not found then raise exception 'Token not found'; end if;
 return true;
end $function$;

revoke all on function strava.agent_token_create(text), strava.agent_token_list(), strava.agent_token_revoke(uuid) from public, anon;
grant execute on function strava.agent_token_create(text), strava.agent_token_list(), strava.agent_token_revoke(uuid) to authenticated;

commit;
