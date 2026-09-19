-- Production definitions of strava.grinder_check_agent_payload and strava.grinder_agent_action,
-- read verbatim with pg_get_functiondef from project kqxasvolwtrczusjhlli on 2026-09-19.
-- Used ONLY by scripts/test-agent-publish.mjs to prove the new tests fail on production code
-- before 006 is applied. Never applied to any live database.
CREATE OR REPLACE FUNCTION strava.grinder_check_agent_payload(payload jsonb)
 RETURNS void LANGUAGE plpgsql SET search_path TO 'strava', 'pg_temp'
AS $function$
declare field text; value jsonb;
begin
 if jsonb_typeof(payload) is distinct from 'object' or octet_length(payload::text)>65536 then raise exception 'Send a grind object under 64 KiB'; end if;
 for field,value in select * from jsonb_each(payload) loop
  if not field=any(array['title','project','harness','turns_typed','duration_s','tool_calls','files_touched','commits','claims','claims_verified','artifacts_produced','started','visibility','rhythm','route','schema_version','measurement_revision','baseline_revision','trace_basis','note','run_id','body','reason','question_id']) then raise exception 'Unsupported public field: %',field; end if;
  if field=any(array['turns_typed','tool_calls','files_touched','commits','claims','claims_verified','artifacts_produced']) and value<>'null'::jsonb then
   if jsonb_typeof(value)<>'number' or (value::text)::numeric<0 or (value::text)::numeric<>floor((value::text)::numeric) or (value::text)::numeric>2147483647 then raise exception 'Counts must be non-negative whole numbers'; end if;
  end if;
 end loop;
 if payload->>'claims_verified' is not null and payload->>'claims' is null then raise exception 'Verified claims require a counted-claims total'; end if;
 if (payload->>'claims_verified')::integer>(payload->>'claims')::integer then raise exception 'Verified claims exceed counted claims'; end if;
 if payload ? 'duration_s' and payload->'duration_s'<>'null'::jsonb and (jsonb_typeof(payload->'duration_s')<>'number' or (payload->>'duration_s')::numeric<0) then raise exception 'Invalid duration'; end if;
 for field in select unnest(array['measurement_revision','baseline_revision']) loop
  if payload->field<>'null'::jsonb and (jsonb_typeof(payload->field)<>'string' or payload->>field!~'^[a-f0-9]{64}$') then raise exception 'Invalid measurement reference'; end if;
 end loop;
 if payload ? 'schema_version' and payload->>'schema_version'<>'1' then raise exception 'Unsupported grind format'; end if;
end $function$;

CREATE OR REPLACE FUNCTION strava.grinder_agent_action(token text, action text, payload jsonb, request_id uuid)
 RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'strava', 'pg_temp'
AS $function$
declare capability grinder_agent_tokens; actor grinder_agents; prior grinder_agent_requests;
 fingerprint text; output jsonb; target runs; result_id uuid; audience text;
begin
 select * into capability from grinder_agent_tokens where token_hash=encode(sha256(convert_to(token,'UTF8')),'hex') for update;
 if not found or capability.revoked or capability.expires_at<=now() then raise exception 'Agent access is unavailable'; end if;
 if action is null or request_id is null then raise exception 'An action and request ID are required'; end if;
 if not action=any(capability.scopes) then raise exception 'This action is outside the granted scope'; end if;
 select * into actor from grinder_agents where id=capability.agent_id;
 perform 1 from profiles where id=actor.owner_id for update;
 perform grinder_check_agent_payload(payload);
 fingerprint=encode(sha256(convert_to(action||payload::text,'UTF8')),'hex');
 select * into prior from grinder_agent_requests r where r.token_id=capability.id and r.request_id=grinder_agent_action.request_id;
 if found then
  if prior.fingerprint<>fingerprint then raise exception 'A request ID cannot be reused for a different action'; end if;
  return prior.response;
 end if;
 if (select count(*) from grinder_agent_requests r join grinder_agent_tokens t on t.id=r.token_id join grinder_agents a on a.id=t.agent_id where a.owner_id=actor.owner_id and r.created_at>now()-interval '1 hour')>=60 then raise exception 'Hourly owner action limit reached'; end if;
 if capability.window_started<now()-interval '1 hour' then
  update grinder_agent_tokens set window_started=now(),window_actions=0 where id=capability.id;
 elsif capability.window_actions>=60 then raise exception 'Hourly action limit reached'; end if;
 if action in ('draft','publish') then
  audience=case when action='draft' then 'private' else coalesce(payload->>'visibility','private') end;
  if not audience=any(capability.audiences) then raise exception 'This audience is outside the granted scope'; end if;
  if audience='public' and actor.visibility<>'public' then raise exception 'Make the agent profile public before public participation'; end if;
  if action='draft' then
   insert into grinder_agent_drafts(owner_id,agent_id,payload) values(actor.owner_id,actor.id,payload) returning id into result_id;
  else
   insert into runs(profile_id,title,project,harness,prompts,duration_s,tool_calls,files_touched,commits,claims,claims_verified,artifacts_produced,visibility,started_at,source_actor_id,agent_name,schema_version,measurement_revision,baseline_revision,rhythm,route,note,trace_basis)
   values(actor.owner_id,left(coalesce(payload->>'title','Agent grind'),200),left(payload->>'project',200),left(payload->>'harness',100),
    (payload->>'turns_typed')::integer,(payload->>'duration_s')::double precision,(payload->>'tool_calls')::integer,
    (payload->>'files_touched')::integer,(payload->>'commits')::integer,(payload->>'claims')::integer,(payload->>'claims_verified')::integer,
    (payload->>'artifacts_produced')::integer,audience,(payload->>'started')::timestamptz,actor.id,actor.name,1,payload->>'measurement_revision',payload->>'baseline_revision',payload->'rhythm',payload->'route',left(payload->>'note',4000),left(payload->>'trace_basis',200)) returning id into result_id;
  end if;
 elsif action in ('reply','ack') then
  select * into target from runs where id=(payload->>'run_id')::uuid;
  if not found then raise exception 'Grind unavailable'; end if;
  audience=case when target.visibility in ('public','anonymous') then 'public' else 'private' end;
  if not audience=any(capability.audiences) or (audience='private' and target.profile_id<>actor.owner_id) then raise exception 'This grind is outside the granted audience'; end if;
  if audience='public' and actor.visibility<>'public' then raise exception 'Make the agent profile public before public participation'; end if;
  if action='reply' then
   insert into grinder_replies(run_id,author_id,body,source_actor_id,agent_name,question_id) values(target.id,actor.owner_id,payload->>'body',actor.id,actor.name,(payload->>'question_id')::uuid) returning id into result_id;
  else
   raise exception 'ack is not exercised by this fixture';
  end if;
 else raise exception 'Unsupported agent action';
 end if;
 output=jsonb_build_object('id',result_id,'action',action,'agent_id',actor.id);
 insert into grinder_agent_requests(token_id,request_id,fingerprint,response) values(capability.id,request_id,fingerprint,output);
 update grinder_agent_tokens set window_actions=window_actions+1 where id=capability.id;
 return output;
end $function$;

-- strava.grinder_profile_id and strava.grinder_issue_agent_token, read verbatim the same way on
-- 2026-09-19. 007 wraps the issuer rather than replacing it, so tests run against this body.
CREATE OR REPLACE FUNCTION strava.grinder_profile_id()
 RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'strava', 'pg_temp'
AS $function$ select id from strava.profiles where auth_uid = auth.uid() limit 1 $function$;

CREATE OR REPLACE FUNCTION strava.grinder_issue_agent_token(agent uuid, allowed_scopes text[], allowed_audiences text[], expires timestamp with time zone)
 RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'strava', 'pg_temp'
AS $function$
declare secret text:='ag_'||gen_random_uuid()::text||gen_random_uuid()::text; token_id uuid;
begin
 perform 1 from profiles where id=grinder_profile_id() for update;
 if not exists(select 1 from grinder_agents where id=agent and owner_id=grinder_profile_id()) then raise exception 'Only the agent owner can grant access'; end if;
 if (select count(*) from grinder_agent_tokens where agent_id=agent and not revoked and expires_at>now())>=5 then raise exception 'Revoke an existing token before issuing another (five active tokens per agent)'; end if;
 if allowed_scopes is null or cardinality(allowed_scopes)<1 or not allowed_scopes <@ array['draft','publish','reply','ack']::text[] then raise exception 'Choose valid action scopes'; end if;
 if allowed_audiences is null or cardinality(allowed_audiences)<1 or not allowed_audiences <@ array['private','public']::text[] then raise exception 'Choose private or public audiences'; end if;
 if expires is null or expires<=now() or expires>now()+interval '90 days' then raise exception 'Choose an expiry within 90 days'; end if;
 insert into grinder_agent_tokens(agent_id,token_hash,scopes,audiences,expires_at)
 values(agent,encode(sha256(convert_to(secret,'UTF8')),'hex'),allowed_scopes,allowed_audiences,expires) returning id into token_id;
 return jsonb_build_object('id',token_id,'token',secret,'expires_at',expires);
end $function$;
