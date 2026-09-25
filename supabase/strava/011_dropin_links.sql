-- 011: drop-in links. A person with no account drops a session file on the landing page, the
-- browser counts it, and "Get a link" stores ONLY the allowlisted counts below plus a title the
-- person typed. No profile, no prompt text, no code, no paths.
--
-- PURELY ADDITIVE. Two new tables and three new functions. No existing table, column, policy,
-- grant or trigger is altered, so no existing row changes who can read it.
--
-- NOT ENUMERABLE. Neither table is granted to anon or authenticated. RLS is on with no policy,
-- so even a stray grant reads nothing. The only doors are the three security definer functions:
-- create (allowlisted payload, rate limited), read one id, delete one id with its secret.
--
-- THE RATE LIMIT HAS TWO LAYERS, AND ONLY ONE IS HARD. The server passes a bucket (the caller's
-- IP). Anyone holding the public anon key can call create directly and pick any bucket, so the
-- per-bucket limit only binds callers who come through /api/link. The GLOBAL caps bind everyone,
-- and they are what bounds storage and abuse. The raw bucket is never stored: only its sha256,
-- and those rows are deleted after 24 hours.
begin;

create table if not exists strava.dropin_links (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '90 days',
  delete_hash text not null check (delete_hash ~ '^[0-9a-f]{64}$'),
  title text not null check (length(title) between 1 and 80),
  harness text not null check (harness in ('Claude Code', 'Cursor', 'Codex')),
  turns_typed integer not null check (turns_typed between 1 and 100000),
  tool_calls integer not null check (tool_calls between 0 and 1000000),
  files_touched integer check (files_touched between 0 and 100000),
  commits integer check (commits between 0 and 10000),
  duration_s integer check (duration_s between 0 and 2592000),
  started_hour smallint check (started_hour between 0 and 23),
  rhythm integer[] not null check (
    cardinality(rhythm) between 1 and 24 and 0 <= all(rhythm) and 100000 >= all(rhythm))
);

create index if not exists dropin_links_created on strava.dropin_links (created_at);

create table if not exists strava.dropin_rate (
  bucket_hash text not null,
  created_at timestamptz not null default now()
);
create index if not exists dropin_rate_bucket on strava.dropin_rate (bucket_hash, created_at);

alter table strava.dropin_links enable row level security;
alter table strava.dropin_rate enable row level security;
revoke all on strava.dropin_links, strava.dropin_rate from public, anon, authenticated;

-- CREATE. Every key of the payload must be on the allowlist; an unknown key is refused, never
-- ignored, so a client that starts sending a new field fails loudly instead of leaking quietly.
create or replace function strava.dropin_create(payload jsonb, bucket text)
 returns jsonb
 language plpgsql
 volatile
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare
  allowed constant text[] := array['title','harness','turns_typed','tool_calls','files_touched',
    'commits','duration_s','started_hour','rhythm'];
  extra text;
  clean text;
  b text := encode(sha256(convert_to(coalesce(bucket, ''), 'UTF8')), 'hex');
  secret text := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
  made strava.dropin_links;
  counts int[];
begin
  if payload is null or jsonb_typeof(payload) <> 'object' then
    raise exception 'Send one run as a JSON object';
  end if;
  if length(payload::text) > 4096 then raise exception 'Send a run under 4 KiB'; end if;
  select k into extra from jsonb_object_keys(payload) k where k <> all(allowed) limit 1;
  if extra is not null then raise exception 'Field not allowed: %', left(extra, 40); end if;

  clean := btrim(regexp_replace(coalesce(payload->>'title', ''), '[[:cntrl:]]+', ' ', 'g'));
  if length(clean) not between 1 and 80 then raise exception 'A title is 1 to 80 characters'; end if;
  -- The title is the one free text field. It may not carry a link, a handle or an address,
  -- because an unlisted page that renders a link is a free spam host.
  if clean ~* '(://|www\.|@|\.(com|net|org|io|co|xyz|ru|cn|app|dev|ly|me|gg|to|link|site|online|shop|top|info|biz)\M)' then
    raise exception 'A title cannot contain a link or an address';
  end if;

  if jsonb_typeof(payload->'rhythm') is distinct from 'array'
     or exists (select 1 from jsonb_array_elements(payload->'rhythm') e(v)
                where jsonb_typeof(e.v) <> 'number' or e.v::text !~ '^[0-9]{1,6}$') then
    raise exception 'rhythm holds whole numbers';
  end if;
  select array_agg(e.v::text::int order by e.n) into counts
    from jsonb_array_elements(payload->'rhythm') with ordinality e(v, n);

  -- Serialise creates so two requests cannot pass a cap together.
  perform pg_advisory_xact_lock(hashtext('strava.dropin_create'));
  delete from dropin_rate where created_at < now() - interval '24 hours';
  if (select count(*) from dropin_links where created_at > now() - interval '1 hour') >= 300
     or (select count(*) from dropin_links where created_at > now() - interval '24 hours') >= 2000 then
    raise exception 'Link limit reached for now. Try again later';
  end if;
  if (select count(*) from dropin_rate where bucket_hash = b and created_at > now() - interval '1 hour') >= 10
     or (select count(*) from dropin_rate where bucket_hash = b) >= 30 then
    raise exception 'Link limit reached for this network. Try again later';
  end if;

  begin
    insert into dropin_links (delete_hash, title, harness, turns_typed, tool_calls, files_touched,
      commits, duration_s, started_hour, rhythm)
    values (encode(sha256(convert_to(secret, 'UTF8')), 'hex'), clean, payload->>'harness',
      (payload->>'turns_typed')::int, (payload->>'tool_calls')::int,
      (payload->>'files_touched')::int, (payload->>'commits')::int,
      (payload->>'duration_s')::int, (payload->>'started_hour')::smallint, counts)
    returning * into made;
  exception
    when check_violation or not_null_violation then raise exception 'These counts are out of range';
    when invalid_text_representation or numeric_value_out_of_range then raise exception 'Counts must be whole numbers';
  end;
  insert into dropin_rate (bucket_hash) values (b);
  -- The secret is returned once. Only its hash is stored, so it cannot be shown again.
  return jsonb_build_object('id', made.id, 'delete_token', secret, 'expires_at', made.expires_at);
end $function$;

-- READ one link by id. Expired links read as missing.
create or replace function strava.dropin_read(link_id uuid)
 returns jsonb
 language sql
 stable
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
  select jsonb_build_object('id', l.id, 'created_at', l.created_at, 'expires_at', l.expires_at,
    'title', l.title, 'harness', l.harness, 'turns_typed', l.turns_typed, 'tool_calls', l.tool_calls,
    'files_touched', l.files_touched, 'commits', l.commits, 'duration_s', l.duration_s,
    'started_hour', l.started_hour, 'rhythm', to_jsonb(l.rhythm))
  from strava.dropin_links l where l.id = link_id and l.expires_at > now()
$function$;

-- DELETE one link with the secret shown at create. A wrong secret and a missing id answer the
-- same, so the function cannot be used to test which ids exist.
create or replace function strava.dropin_delete(link_id uuid, token text)
 returns boolean
 language plpgsql
 volatile
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
begin
  if token is null or token !~ '^[0-9a-f]{64}$' then return false; end if;
  delete from dropin_links where id = link_id
    and delete_hash = encode(sha256(convert_to(token, 'UTF8')), 'hex');
  return found;
end $function$;

revoke all on function strava.dropin_create(jsonb, text) from public, anon, authenticated;
revoke all on function strava.dropin_read(uuid) from public, anon, authenticated;
revoke all on function strava.dropin_delete(uuid, text) from public, anon, authenticated;
grant execute on function strava.dropin_create(jsonb, text) to anon, authenticated;
grant execute on function strava.dropin_read(uuid) to anon, authenticated;
grant execute on function strava.dropin_delete(uuid, text) to anon, authenticated;

notify pgrst, 'reload schema';
commit;
