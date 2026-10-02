-- Capture is a locally measured source, not independent proof of human work.
-- Preserve historical rows. Every new run needs a capture; every update freezes its facts.
begin;

create or replace function strava.run_capture_guard() returns trigger
language plpgsql security definer set search_path = strava, pg_temp as $$
declare field text; trace jsonb;
begin
 if tg_op='INSERT' then
  if new.measurement_revision is null or new.measurement_revision !~ '^[a-f0-9]{64}$'
     or new.schema_version is distinct from 1 or lower(new.harness) not in ('claude code','claude-agent','cursor','codex','grok bot') or new.harness is null
     or new.trace_basis is null or new.trace_basis not in
       ('elapsed','position','typed-turn order','elapsed-agent-tool-calls','timestamped native events','timestamps unavailable',
        'typed-turn order; spacing is not elapsed time; sessions split on human-turn gaps, not measured idle',
        'typed-turn order; Grok Bot export has no top-level event timestamps')
     or (jsonb_typeof(new.rhythm) is distinct from 'array' and jsonb_typeof(new.ridge) is distinct from 'array') then
   raise exception 'Import a recorded session before saving a run. Manual runs are not supported.';
  end if;
  trace:=case when jsonb_typeof(new.rhythm)='array' and jsonb_array_length(new.rhythm)>0 then new.rhythm else new.ridge end;
  if jsonb_typeof(trace) is distinct from 'array' or jsonb_array_length(trace) not between 1 and 1000 then
   raise exception 'Import a recorded session with an activity trace.';
  end if;
  if exists(select 1 from jsonb_array_elements(trace) v where strava.grinder_is_safe_count(v) is not true)
     or not exists(select 1 from jsonb_array_elements(trace) v where jsonb_typeof(v)='number' and (v::text)::numeric>0) then
   raise exception 'The recorded session must contain activity.';
  end if;
  if new.image_url is not null then raise exception 'Use Add photos to upload a photo for this run.'; end if;
  if new.visibility <> 'private' or coalesce(new.crew_shared,false) then
   raise exception 'New sessions start private. Review the saved run before sharing it.';
  end if;
 else
  if new.image_url is distinct from old.image_url and new.image_url is not null then
   raise exception 'Use Add photos to upload a photo for this run.';
  end if;
  foreach field in array array['id','profile_id','created_at','started_at','harness','model','schema_version',
   'measurement_revision','baseline_revision','trace_basis','prompts','duration_s','wall_time_s',
   'tool_calls','shell_calls','files_touched','commits','claims','claims_verified','artifacts_produced',
   'rhythm','route','tool_mix','ridge','worker_bins','commit_bins','ridge_basis','ridge_wall_seconds',
   'ridge_tool_calls','source_actor_id','agent_name','code_route','progress_delta'] loop
   if to_jsonb(new)->field is distinct from to_jsonb(old)->field then
    raise exception 'Recorded session facts cannot be edited. Edit the description, photos or audience instead.';
   end if;
  end loop;
 end if;
 return new;
end $$;
revoke all on function strava.run_capture_guard() from public,anon,authenticated;
drop trigger if exists run_capture_guard on strava.runs;
create trigger run_capture_guard before insert or update on strava.runs
 for each row execute function strava.run_capture_guard();

-- Existing index is also included here so this migration does not rely on a client lookup.
create unique index if not exists runs_profile_measurement_revision_unique
 on strava.runs(profile_id,measurement_revision) where measurement_revision is not null;

-- An owner may deliberately share a run captured by their private Connect agent. This does
-- not make the agent public and does not widen its token audiences; token RPCs still check
-- those capabilities before INSERT. Preserve the existing count/attribution constraints.
create or replace function strava.grinder_run_contract_guard() returns trigger
language plpgsql security definer set search_path=strava,pg_temp as $$
begin
 if new.claims_verified is not null and new.claims is null then raise exception 'Verified claims require a counted-claims total'; end if;
 if new.prompts<0 or new.tool_calls<0 or new.files_touched<0 or new.commits<0 or new.claims<0 or new.claims_verified<0 or new.artifacts_produced<0 or new.claims_verified>new.claims then raise exception 'Grind counts must be non-negative and supported counts cannot exceed claims'; end if;
 if new.duration_s<0 or new.duration_s in ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8) then raise exception 'Invalid grind duration'; end if;
 if new.schema_version is not null and new.schema_version<>1 then raise exception 'Unsupported grind format'; end if;
 if new.measurement_revision is not null and new.measurement_revision!~'^[a-f0-9]{64}$' or new.baseline_revision is not null and new.baseline_revision!~'^[a-f0-9]{64}$' then raise exception 'Invalid measurement reference'; end if;
 if new.source_actor_id is not null and not exists(select 1 from strava.grinder_agents where id=new.source_actor_id and owner_id=new.profile_id
   and (visibility='public' or new.visibility='private' or new.profile_id=strava.grinder_profile_id())) then
  raise exception 'Choose an owned agent with matching visibility';
 end if;
 if new.rig_revision is not null and not exists(select 1 from strava.grinder_rig_revisions where id=new.rig_revision and (visibility='public' or (owner_id=new.profile_id and new.visibility='private'))) then raise exception 'Rig is unavailable to this audience'; end if;
 return new;
end $$;
revoke all on function strava.grinder_run_contract_guard() from public,anon,authenticated;
commit;
