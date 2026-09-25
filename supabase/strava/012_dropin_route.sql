-- THE RUN MAP ON A DROP-IN LINK. A card made from a dropped session file (011) carried counts and
-- an activity line. This adds the route the run took through the folders it touched: a list of
-- small whole numbers, one station index per move, nothing else. No folder name, no path and no
-- file name is stored or accepted; the browser reader (site/dropin-parse.js) and the Python
-- readers (agentgrinder/ingest.py) both send indices only, and the check below refuses anything
-- that is not a short array of small integers.
--
-- Additive. The column is optional so a client that predates it still creates links. The create
-- and read functions are replaced in full (the allowlist gains one word, route); the delete
-- function, the rate table and every policy stay as 011 left them.
begin;

alter table strava.dropin_links add column if not exists route smallint[]
  check (route is null or (cardinality(route) between 1 and 400 and 0 <= all(route) and 15 >= all(route)));

create or replace function strava.dropin_create(payload jsonb, bucket text)
 returns jsonb
 language plpgsql
 volatile
 security definer
 set search_path to 'strava', 'pg_temp'
as $function$
declare
  allowed constant text[] := array['title','harness','turns_typed','tool_calls','files_touched',
    'commits','duration_s','started_hour','rhythm','route'];
  extra text;
  clean text;
  b text := encode(sha256(convert_to(coalesce(bucket, ''), 'UTF8')), 'hex');
  secret text := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
  made strava.dropin_links;
  counts int[];
  moves smallint[];
begin
  if payload is null or jsonb_typeof(payload) <> 'object' then
    raise exception 'Send one run as a JSON object';
  end if;
  if length(payload::text) > 4096 then raise exception 'Send a run under 4 KiB'; end if;
  select k into extra from jsonb_object_keys(payload) k where k <> all(allowed) limit 1;
  if extra is not null then raise exception 'Field not allowed: %', left(extra, 40); end if;

  clean := btrim(regexp_replace(coalesce(payload->>'title', ''), '[[:cntrl:]]+', ' ', 'g'));
  if length(clean) not between 1 and 80 then raise exception 'A title is 1 to 80 characters'; end if;
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

  -- The route: absent, null, or an array of station indices 0 to 15. A string anywhere in it is
  -- refused, so a folder name cannot arrive by this door.
  if payload ? 'route' and jsonb_typeof(payload->'route') <> 'null' then
    if jsonb_typeof(payload->'route') <> 'array'
       or exists (select 1 from jsonb_array_elements(payload->'route') e(v)
                  where jsonb_typeof(e.v) <> 'number' or e.v::text !~ '^[0-9]{1,2}$') then
      raise exception 'route holds small whole numbers';
    end if;
    select array_agg(e.v::text::smallint order by e.n) into moves
      from jsonb_array_elements(payload->'route') with ordinality e(v, n);
  end if;

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
      commits, duration_s, started_hour, rhythm, route)
    values (encode(sha256(convert_to(secret, 'UTF8')), 'hex'), clean, payload->>'harness',
      (payload->>'turns_typed')::int, (payload->>'tool_calls')::int,
      (payload->>'files_touched')::int, (payload->>'commits')::int,
      (payload->>'duration_s')::int, (payload->>'started_hour')::smallint, counts, moves)
    returning * into made;
  exception
    when check_violation or not_null_violation then raise exception 'These counts are out of range';
    when invalid_text_representation or numeric_value_out_of_range then raise exception 'Counts must be whole numbers';
  end;
  insert into dropin_rate (bucket_hash) values (b);
  return jsonb_build_object('id', made.id, 'delete_token', secret, 'expires_at', made.expires_at);
end $function$;

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
    'started_hour', l.started_hour, 'rhythm', to_jsonb(l.rhythm), 'route', to_jsonb(l.route))
  from strava.dropin_links l where l.id = link_id and l.expires_at > now()
$function$;

revoke all on function strava.dropin_create(jsonb, text) from public, anon, authenticated;
revoke all on function strava.dropin_read(uuid) from public, anon, authenticated;
grant execute on function strava.dropin_create(jsonb, text) to anon, authenticated;
grant execute on function strava.dropin_read(uuid) to anon, authenticated;

notify pgrst, 'reload schema';
commit;
