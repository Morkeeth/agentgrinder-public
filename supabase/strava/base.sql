-- Strava base tables, derived from the inherited schema-only snapshot.
-- Applied only inside the new strava schema by prepare-strava-database.py.
CREATE TABLE "profiles" ("id" uuid NOT NULL DEFAULT gen_random_uuid(),
"auth_uid" uuid,
"github_handle" text,
"name" text,
"rig" jsonb NOT NULL DEFAULT '{}'::jsonb,
"created_at" timestamp with time zone NOT NULL DEFAULT now());
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_pkey" PRIMARY KEY (id);
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_auth_uid_key" UNIQUE (auth_uid);
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_github_handle_key" UNIQUE (github_handle);
ALTER TABLE "profiles" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_read" ON "profiles" AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY "profiles_owner_write" ON "profiles" AS PERMISSIVE FOR ALL TO public USING ((auth_uid = auth.uid())) WITH CHECK ((auth_uid = auth.uid()));
CREATE TABLE "runs" ("id" uuid NOT NULL DEFAULT gen_random_uuid(),
"profile_id" uuid NOT NULL,
"title" text NOT NULL,
"project" text,
"harness" text,
"started_at" timestamp with time zone,
"duration_s" integer,
"prompts" integer,
"tool_calls" integer,
"files_touched" integer,
"commits" integer,
"rhythm" jsonb,
"is_ship" boolean NOT NULL DEFAULT false,
"visibility" text NOT NULL DEFAULT 'private'::text,
"created_at" timestamp with time zone NOT NULL DEFAULT now(),
"note" text,
"route" jsonb,
"tool_mix" jsonb,
"claims" integer,
"claims_verified" integer,
"artifacts_produced" integer,
"coach_verdict" text,
"coach_plan" text,
"coach_tool_calls" integer,
"progress_verdict" text,
"reach" boolean);
ALTER TABLE "runs" ADD CONSTRAINT "runs_pkey" PRIMARY KEY (id);
ALTER TABLE "runs" ADD CONSTRAINT "runs_profile_id_fkey" FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE "runs" ADD CONSTRAINT "runs_visibility_check" CHECK ((visibility = ANY (ARRAY['private'::text, 'link'::text, 'public'::text, 'crew'::text, 'anonymous'::text])));
ALTER TABLE "runs" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "runs_owner_write" ON "runs" AS PERMISSIVE FOR ALL TO public USING ((profile_id IN ( SELECT profiles.id
 FROM profiles
 WHERE (profiles.auth_uid = auth.uid())))) WITH CHECK ((profile_id IN ( SELECT profiles.id
 FROM profiles
 WHERE (profiles.auth_uid = auth.uid()))));
CREATE POLICY "runs_read" ON "runs" AS PERMISSIVE FOR SELECT TO public USING (((visibility = ANY (ARRAY['public'::text, 'link'::text, 'anonymous'::text])) OR (profile_id IN ( SELECT profiles.id
 FROM profiles
 WHERE (profiles.auth_uid = auth.uid())))));
CREATE TABLE "acks" ("id" uuid NOT NULL DEFAULT gen_random_uuid(),
"from_profile" uuid NOT NULL,
"to_profile" uuid NOT NULL,
"run_id" uuid NOT NULL,
"reason" text NOT NULL,
"note" text,
"same_owner" boolean NOT NULL DEFAULT false,
"created_at" timestamp with time zone NOT NULL DEFAULT now());
ALTER TABLE "acks" ADD CONSTRAINT "acks_reason_check" CHECK ((reason = ANY (ARRAY['solved'::text, 'checked'::text, 'helped'::text, 'explained'::text, 'recovered'::text, 'shipped'::text])));
ALTER TABLE "acks" ADD CONSTRAINT "acks_pkey" PRIMARY KEY (id);
ALTER TABLE "acks" ADD CONSTRAINT "acks_from_profile_fkey" FOREIGN KEY (from_profile) REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE "acks" ADD CONSTRAINT "acks_to_profile_fkey" FOREIGN KEY (to_profile) REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE "acks" ADD CONSTRAINT "acks_run_id_fkey" FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE;
ALTER TABLE "acks" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "acks_read" ON "acks" AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY "acks_write" ON "acks" AS PERMISSIVE FOR INSERT TO public WITH CHECK ((from_profile IN ( SELECT profiles.id
 FROM profiles
 WHERE (profiles.auth_uid = auth.uid()))));
