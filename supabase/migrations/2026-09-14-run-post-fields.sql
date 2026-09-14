begin;

-- Builder-authored context for the social card. These fields are never inferred from
-- measurements or transcript text.
alter table public.runs
  add column if not exists caption text,
  add column if not exists output_url text;

alter table public.runs
  drop constraint if exists runs_caption_length,
  add constraint runs_caption_length
    check (caption is null or length(trim(caption)) between 1 and 280),
  drop constraint if exists runs_output_url_format,
  add constraint runs_output_url_format
    check (
      output_url is null
      or (
        length(output_url) <= 2048
        and output_url ~ '^https?://[^[:space:]]+$'
      )
    );

comment on column public.runs.caption is
  'Short builder-authored caption; never generated from measurements';
comment on column public.runs.output_url is
  'Optional builder-supplied http(s) link to the recorded output';

-- Owners already pass the restrictive run ownership policy. Keep edits
-- column-scoped so changing social context cannot change attribution.
grant update(caption, output_url) on public.runs to authenticated;

commit;
