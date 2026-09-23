-- 011: STRIVE Connect. Connect once, sync forever.
--
-- Three parts, all inside the strava schema:
--   S0  a pairing funnel that records steps and nothing else. No content column exists, so no
--       prompt, path, transcript line or user code can be written to it even by mistake.
--   S1  device pairing as RFC 8628 (the flow `gh auth login` uses): the device asks for a code,
--       a signed-in human approves it on a phone, the device polls and claims one token.
--   S2  the device token is a sliding 90 day credential that renews on use, with last_seen_at
--       per token so Connections can say when a device last synced.
--
-- Secrets: only sha256 hashes of the device code and the user code are stored. The plaintext
-- device code is returned once to the device, the user code once to the device to display.
-- Reverse with supabase/strava/down/011_connect_device.sql.

begin;

-- One pairing attempt. profile_id stays null until a human decides, so a pending pairing is
-- not attached to anybody. device_name and harness are declared by the device and shown on the
-- approve page; both are short and path-free, checked below.
create table if not exists strava.connect_pairings (
  id uuid primary key default gen_random_uuid(),
  device_code_hash text not null unique,
  user_code_hash text not null unique,
  harness text not null check (harness in ('cursor','codex','claude','grokbot','other')),
  device_name text not null check (length(device_name) between 1 and 40),
  scopes text[] not null check (cardinality(scopes) between 1 and 2 and scopes <@ array['draft','publish']::text[]),
  status text not null default 'pending' check (status in ('pending','approved','denied','claimed','expired')),
  profile_id uuid references strava.profiles(id) on delete cascade,
  token_id uuid references strava.grinder_agent_tokens(id) on delete set null,
  interval_seconds integer not null default 5 check (interval_seconds between 1 and 60),
  expires_at timestamptz not null,
  last_polled_at timestamptz,
  decided_at timestamptz,
  claimed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists connect_pairings_status_expiry on strava.connect_pairings (status, expires_at);
create index if not exists connect_pairings_token on strava.connect_pairings (token_id);

-- S0. A funnel row is a pairing, a step name and a time. There is deliberately no payload,
-- label, address or count column: this table cannot carry content.
--
-- The five steps of a completed pairing are connect_started, code_issued, code_approved,
-- token_claimed and first_run_received. A pairing that ends without an approval records exactly
-- one terminal step instead - code_denied when the human denies, code_expired when the window
-- closes - so an abandoned pairing is three rows and is never confused with a stalled one.
create table if not exists strava.connect_funnel_events (
  -- An identity column, not a uuid: the step order of one pairing is the point of a funnel, and
  -- connect_started and code_issued share a timestamp to the microsecond.
  id bigint generated always as identity primary key,
  pairing_id uuid not null references strava.connect_pairings(id) on delete cascade,
  event text not null check (event in ('connect_started','code_issued','code_approved','token_claimed','first_run_received','code_denied','code_expired')),
  created_at timestamptz not null default now(),
  unique (pairing_id, event)
);

-- Neither table is exposed to a client. Every read and write goes through the security definer
-- functions below, so RLS is on with no policy: anon and authenticated reach nothing directly.
alter table strava.connect_pairings enable row level security;
alter table strava.connect_funnel_events enable row level security;
revoke all on strava.connect_pairings from public, anon, authenticated;
revoke all on strava.connect_funnel_events from public, anon, authenticated;

-- S2. When a device last used its credential. Null means it has never uploaded a run.
alter table strava.grinder_agent_tokens add column if not exists last_seen_at timestamptz;

create or replace function strava.connect_code_hash(p_code text)
 returns text
 language sql
 immutable
 set search_path to 'strava', 'pg_temp'
as $function$ select encode(sha256(convert_to(p_code,'UTF8')),'hex') $function$;

-- RFC 8628 section 6.1: a user code the human retypes uses a small alphabet with no vowels and
-- no digits, so O/0 and I/1 cannot be confused. Eight characters is 20^8, about 34 bits, and the
-- code lives for 900 seconds.
create or replace function strava.connect_user_code()
 returns text
 language plpgsql
 set search_path to 'strava', 'pg_temp'
as $function$
declare alphabet constant text := 'BCDFGHJKLMNPQRSTVWXZ'; pool text := ''; code text := ''; byte integer;
begin
 while length(code) < 8 loop
  if length(pool) < 2 then pool := pool || replace(gen_random_uuid()::text,'-',''); end if;
  byte := ('x' || substr(pool,1,2))::bit(8)::integer;
  pool := substr(pool,3);
  -- Reject the top 16 byte values so all twenty letters stay equally likely.
  if byte < 240 then code := code || substr(alphabet, 1 + (byte % 20), 1); end if;
 end loop;
 return code;
end $function$;

create or replace function strava.connect_funnel_note(p_pairing uuid, p_event text)
 returns void
 language sql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
 insert into strava.connect_funnel_events(pairing_id,event) values(p_pairing,p_event)
 on conflict (pairing_id,event) do nothing
$function$;

-- Mark pending pairings whose window has closed and record the terminal step once.
create or replace function strava.connect_sweep_expired()
 returns integer
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare closed uuid; swept integer := 0;
begin
 for closed in
  update strava.connect_pairings set status='expired'
   where status='pending' and expires_at<=now()
   returning id
 loop
  perform strava.connect_funnel_note(closed,'code_expired');
  swept := swept + 1;
 end loop;
 return swept;
end $function$;

-- S1 step one: the device asks for a code. No account is involved yet, so anon may call this.
-- The plaintext device code and user code are returned once and never stored.
create or replace function strava.connect_device_start(p_harness text, p_device_name text, p_scopes text[])
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare device_code text; user_code text; clean_name text := trim(coalesce(p_device_name,''));
 want text[] := coalesce(p_scopes, array['draft','publish']::text[]); pairing uuid; attempt integer := 0;
 window_seconds constant integer := 900; poll_interval constant integer := 5;
begin
 if p_harness is null or p_harness <> all(array['cursor','codex','claude','grokbot','other']) then
  raise exception 'Name the harness asking to connect'; end if;
 if length(clean_name) not between 1 and 40 then raise exception 'A device name is 1 to 40 characters'; end if;
 -- A device name is a name, not a location. No separator, so no home directory or path reaches
 -- the approve page or the funnel.
 if clean_name ~ '[/\\]' or clean_name ~ '^~' then raise exception 'A device name carries no file path'; end if;
 if cardinality(want) < 1 or not want <@ array['draft','publish']::text[] then
  raise exception 'Device pairing grants draft and publish only'; end if;
 -- Burst guard. Deliberately short so an abandoned flood cannot keep a real device out for long.
 if (select count(*) from strava.connect_pairings where created_at > now() - interval '1 minute') >= 120 then
  raise exception 'Too many connection requests just now. Try again in a minute'; end if;
 device_code := 'dc_' || gen_random_uuid()::text || gen_random_uuid()::text;
 loop
  attempt := attempt + 1;
  user_code := strava.connect_user_code();
  exit when not exists (select 1 from strava.connect_pairings where user_code_hash = strava.connect_code_hash(user_code));
  if attempt >= 8 then raise exception 'Could not allocate a user code. Try again'; end if;
 end loop;
 insert into strava.connect_pairings(device_code_hash,user_code_hash,harness,device_name,scopes,interval_seconds,expires_at)
 values(strava.connect_code_hash(device_code),strava.connect_code_hash(user_code),p_harness,clean_name,want,
        poll_interval,now() + make_interval(secs => window_seconds))
 returning id into pairing;
 perform strava.connect_funnel_note(pairing,'connect_started');
 perform strava.connect_funnel_note(pairing,'code_issued');
 return jsonb_build_object('device_code',device_code,'user_code',user_code,
  'expires_in',window_seconds,'interval',poll_interval);
end $function$;

-- S1 step two: the approve page reads what it is about to grant. Signed in only, and it returns
-- the device's own declared name and harness, never who asked or from where.
create or replace function strava.connect_pairing_view(p_user_code text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare pairing strava.connect_pairings;
begin
 if strava.grinder_profile_id() is null then raise exception 'Sign in to approve a device'; end if;
 select * into pairing from strava.connect_pairings
  where user_code_hash = strava.connect_code_hash(upper(trim(coalesce(p_user_code,''))));
 if not found then raise exception 'That code is not one of ours. Check the eight characters'; end if;
 if pairing.status='pending' and pairing.expires_at<=now() then
  update strava.connect_pairings set status='expired' where id=pairing.id;
  perform strava.connect_funnel_note(pairing.id,'code_expired');
  pairing.status := 'expired';
 end if;
 return jsonb_build_object('harness',pairing.harness,'device_name',pairing.device_name,
  'scopes',to_jsonb(pairing.scopes),'audiences',to_jsonb(array['private']::text[]),'status',pairing.status,
  'expires_in',greatest(0,floor(extract(epoch from pairing.expires_at - now()))::integer),
  'decided_by_me',pairing.profile_id is not null and pairing.profile_id=strava.grinder_profile_id());
end $function$;

-- S1 step three: Approve or Deny. One decision per code; a second attempt is refused, so a code
-- cannot be approved twice and a denied code can never become an approved one.
create or replace function strava.connect_pairing_decide(p_user_code text, p_approve boolean)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare me uuid := strava.grinder_profile_id(); pairing strava.connect_pairings;
begin
 if me is null then raise exception 'Sign in to approve a device'; end if;
 if p_approve is null then raise exception 'Choose Approve or Deny'; end if;
 select * into pairing from strava.connect_pairings
  where user_code_hash = strava.connect_code_hash(upper(trim(coalesce(p_user_code,'')))) for update;
 if not found then raise exception 'That code is not one of ours. Check the eight characters'; end if;
 if pairing.status='pending' and pairing.expires_at<=now() then
  update strava.connect_pairings set status='expired' where id=pairing.id;
  perform strava.connect_funnel_note(pairing.id,'code_expired');
  raise exception 'That code expired. Start the connection again on the device';
 end if;
 if pairing.status='expired' then raise exception 'That code expired. Start the connection again on the device'; end if;
 if pairing.status<>'pending' then raise exception 'That code has already been used'; end if;
 if p_approve then
  -- Serialise per profile so two approvals cannot pass the device cap together.
  perform 1 from strava.profiles where id=me for update;
  if (select count(*) from strava.grinder_agent_tokens t join strava.grinder_agents a on a.id=t.agent_id
      where a.owner_id=me and t.label is not null and not t.revoked and t.expires_at>now()) >= 5 then
   raise exception 'Revoke a connected device before adding another (five active)'; end if;
  update strava.connect_pairings set status='approved',profile_id=me,decided_at=now() where id=pairing.id;
  perform strava.connect_funnel_note(pairing.id,'code_approved');
 else
  update strava.connect_pairings set status='denied',profile_id=me,decided_at=now() where id=pairing.id;
  perform strava.connect_funnel_note(pairing.id,'code_denied');
 end if;
 return jsonb_build_object('status',case when p_approve then 'approved' else 'denied' end,
  'device_name',pairing.device_name,'harness',pairing.harness);
end $function$;

-- S1 step four: the device polls. RFC 8628 section 3.5 answers: authorization_pending while the
-- human has not decided, slow_down when the device polls faster than the interval it was given,
-- access_denied after a Deny, expired_token after the window, invalid_grant for a code we do not
-- hold or have already answered with a token, and the credential exactly once.
create or replace function strava.connect_device_poll(p_device_code text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare pairing strava.connect_pairings; owner_agent uuid; secret text; minted uuid;
 lifetime constant interval := interval '90 days';
begin
 select * into pairing from strava.connect_pairings
  where device_code_hash = strava.connect_code_hash(coalesce(p_device_code,'')) for update;
 if not found then return jsonb_build_object('error','invalid_grant'); end if;
 -- Interval first, and a refused poll does not move the clock, so a tight loop is answered
 -- without ever locking a well-behaved device out.
 if pairing.last_polled_at is not null
    and now() < pairing.last_polled_at + make_interval(secs => pairing.interval_seconds) then
  return jsonb_build_object('error','slow_down','interval',pairing.interval_seconds);
 end if;
 update strava.connect_pairings set last_polled_at=now() where id=pairing.id;
 if pairing.status='denied' then return jsonb_build_object('error','access_denied'); end if;
 if pairing.status='claimed' then return jsonb_build_object('error','invalid_grant'); end if;
 if pairing.status='expired' then return jsonb_build_object('error','expired_token'); end if;
 if pairing.expires_at<=now() then
  update strava.connect_pairings set status='expired' where id=pairing.id;
  perform strava.connect_funnel_note(pairing.id,'code_expired');
  return jsonb_build_object('error','expired_token');
 end if;
 if pairing.status='pending' then return jsonb_build_object('error','authorization_pending'); end if;
 -- Approved. Mint the device credential in the same shape the upload endpoint already accepts.
 select id into owner_agent from strava.grinder_agents
  where owner_id=pairing.profile_id and name='Connect' order by created_at limit 1;
 if owner_agent is null then
  insert into strava.grinder_agents(owner_id,name,visibility) values(pairing.profile_id,'Connect','private')
  returning id into owner_agent;
 end if;
 secret := 'ag_' || gen_random_uuid()::text || gen_random_uuid()::text;
 insert into strava.grinder_agent_tokens(agent_id,token_hash,scopes,audiences,expires_at,label,token_prefix)
 values(owner_agent,strava.connect_code_hash(secret),pairing.scopes,array['private']::text[],
        now() + lifetime,pairing.device_name,left(secret,8))
 returning id into minted;
 update strava.connect_pairings set status='claimed',token_id=minted,claimed_at=now() where id=pairing.id;
 perform strava.connect_funnel_note(pairing.id,'token_claimed');
 return jsonb_build_object('access_token',secret,'token_type','bearer',
  'expires_in',floor(extract(epoch from lifetime))::integer,'scope',array_to_string(pairing.scopes,' '));
end $function$;

-- S2. Every accepted agent action inserts exactly one grinder_agent_requests row, so that insert
-- is the one honest record of a credential being used. A device token (one with a label, minted
-- by Connect) slides its expiry forward 90 days on each use; an Advanced Agents token keeps the
-- fixed expiry its owner chose. The first run through a paired device closes the funnel.
create or replace function strava.connect_token_touch()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare paired uuid;
begin
 update strava.grinder_agent_tokens
    set last_seen_at = now(),
        expires_at = case when label is not null then greatest(expires_at, now() + interval '90 days')
                          else expires_at end
  where id = new.token_id;
 if new.response->>'action' in ('draft','publish') then
  select id into paired from strava.connect_pairings where token_id = new.token_id;
  if paired is not null then perform strava.connect_funnel_note(paired,'first_run_received'); end if;
 end if;
 return new;
end $function$;

drop trigger if exists connect_token_touch on strava.grinder_agent_requests;
create trigger connect_token_touch after insert on strava.grinder_agent_requests
 for each row execute function strava.connect_token_touch();

-- S2. The browser Connect form mints the same sliding 90 day credential as a paired device.
-- Unchanged from 007 otherwise: private draft and publish, five active per profile.
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
 perform 1 from strava.profiles where id=me for update;
 if (select count(*) from strava.grinder_agent_tokens t join strava.grinder_agents a on a.id=t.agent_id
     where a.owner_id=me and t.label is not null and not t.revoked and t.expires_at>now())>=5 then
  raise exception 'Revoke a connected agent before adding another (five active)';
 end if;
 select id into connect_agent from strava.grinder_agents where owner_id=me and name='Connect' order by created_at limit 1;
 if connect_agent is null then
  insert into strava.grinder_agents(owner_id,name,visibility) values(me,'Connect','private') returning id into connect_agent;
 end if;
 issued=strava.grinder_issue_agent_token(connect_agent,array['draft','publish'],array['private'],now()+interval '90 days');
 update strava.grinder_agent_tokens set label=clean,token_prefix=left(issued->>'token',8)
  where id=(issued->>'id')::uuid returning * into minted;
 return jsonb_build_object('id',minted.id,'label',minted.label,'token',issued->>'token','token_prefix',minted.token_prefix,
  'created_at',minted.created_at,'expires_at',minted.expires_at,'scopes',to_jsonb(minted.scopes),'audiences',to_jsonb(minted.audiences));
end $function$;

-- S2. Connections lists devices with when each last synced. A device with no run in seven days
-- is stale, which the page shows in amber; one that has never synced is waiting, not stale,
-- until its own first week passes.
create or replace function strava.agent_token_list()
 returns jsonb
 language sql
 stable
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
 select coalesce(jsonb_agg(jsonb_build_object('id',t.id,'label',t.label,'token_prefix',t.token_prefix,'created_at',t.created_at,
   'expires_at',t.expires_at,'revoked',t.revoked,'scopes',to_jsonb(t.scopes),'audiences',to_jsonb(t.audiences),
   'last_seen_at',t.last_seen_at,'harness',p.harness,'device_name',coalesce(p.device_name,t.label),
   'paired',p.id is not null,
   'stale',not t.revoked and t.expires_at>now() and coalesce(t.last_seen_at,t.created_at) < now() - interval '7 days')
   order by t.created_at desc),'[]'::jsonb)
 from strava.grinder_agent_tokens t
 join strava.grinder_agents a on a.id=t.agent_id
 left join strava.connect_pairings p on p.token_id=t.id
 where a.owner_id=strava.grinder_profile_id() and t.label is not null
$function$;

revoke all on function strava.connect_code_hash(text), strava.connect_user_code(),
 strava.connect_funnel_note(uuid,text), strava.connect_token_touch(),
 strava.connect_sweep_expired(), strava.connect_device_start(text,text,text[]),
 strava.connect_device_poll(text), strava.connect_pairing_view(text),
 strava.connect_pairing_decide(text,boolean) from public, anon, authenticated;
-- The device has no account: the pairing request and its polls run with the public anon key.
grant execute on function strava.connect_device_start(text,text,text[]), strava.connect_device_poll(text) to anon, authenticated;
-- Approving, denying and sweeping need a signed-in human.
grant execute on function strava.connect_pairing_view(text), strava.connect_pairing_decide(text,boolean),
 strava.connect_sweep_expired() to authenticated;

commit;
