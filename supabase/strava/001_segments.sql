begin;

create table if not exists strava.segments (
  id text primary key,
  name text not null,
  description text not null,
  task_url text not null,
  repo_url text not null,
  created_at timestamptz not null default now(),
  constraint segments_id_format check (id ~ '^segment-[0-9]{2}$'),
  constraint segments_name_length check (length(trim(name)) between 1 and 120),
  constraint segments_task_url_format check (task_url ~ '^https://'),
  constraint segments_repo_url_format check (repo_url ~ '^https://')
);

alter table strava.segments enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'strava'
      and tablename = 'segments'
      and policyname = 'segments_read'
  ) then
    create policy "segments_read"
      on strava.segments
      for select
      to anon, authenticated
      using (true);
  end if;
end
$$;

grant select on strava.segments to anon, authenticated;

insert into strava.segments (id, name, description, task_url, repo_url)
values (
  'segment-01',
  'Add a --json flag to a small CLI',
  'Add machine-readable output to the bundled forty-line Python summary CLI.',
  'https://github.com/Morkeeth/agentgrinder-public/blob/main/samples/segment-01/TASK.md',
  'https://github.com/Morkeeth/agentgrinder-public/tree/main/samples/segment-01'
)
on conflict (id) do update set
  name = excluded.name,
  description = excluded.description,
  task_url = excluded.task_url,
  repo_url = excluded.repo_url;

alter table strava.runs
  add column if not exists segment_id text,
  add column if not exists model text,
  add column if not exists wall_time_s integer;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'strava.runs'::regclass
      and conname = 'runs_segment_id_fkey'
  ) then
    alter table strava.runs
      add constraint runs_segment_id_fkey
      foreign key (segment_id) references strava.segments(id) on delete set null;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'strava.runs'::regclass
      and conname = 'runs_model_length'
  ) then
    alter table strava.runs
      add constraint runs_model_length
      check (model is null or length(trim(model)) between 1 and 120);
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'strava.runs'::regclass
      and conname = 'runs_wall_time_nonnegative'
  ) then
    alter table strava.runs
      add constraint runs_wall_time_nonnegative
      check (wall_time_s is null or wall_time_s >= 0);
  end if;
end
$$;

comment on column strava.runs.segment_id is
  'Optional fixed public task this run was recorded against';
comment on column strava.runs.model is
  'Optional builder-reported model label; unknown when absent';
comment on column strava.runs.wall_time_s is
  'Optional elapsed segment task time in seconds; distinct from moving time';

commit;
