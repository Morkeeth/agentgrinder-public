# Live review · Grok private preview · 2026-09-15

Reviewed locally from PR #16 head `cdabc43` on
`cursor/finish-first-user-journey-02d5`. PR #16 was open when this review began.
Nothing was posted, saved, deployed or written to a hosted service.

## Commands run

```sh
python3 scripts/dev.py setup
sudo apt-get update
sudo apt-get install -y python3.12-venv
python3 scripts/dev.py setup
python3 -c "import shutil; shutil.rmtree('.venv', ignore_errors=True)"
python3 scripts/dev.py setup
python3 templates/grokbot/post-agent-run/scripts/preview.py samples/sample_grokbot_bot_activity.jsonl
python3 templates/grokbot/post-agent-run/scripts/preview.py samples/sample_grokbot_safe_real_shape.jsonl
python3 scripts/dev.py serve
```

The first setup failed because this Ubuntu image did not include
`python3.12-venv`. Installing it left the first, incomplete `.venv` without
pip, so the environment had to be removed and setup rerun. The final setup
completed.

## Exact preview stdout · metrics only

`samples/sample_grokbot_bot_activity.jsonl`:

```json
{
  "harness": "Grok Bot",
  "is_sample": true,
  "activity_label": "bot activity",
  "project": "session",
  "turns_typed": 2,
  "tool_calls": 3,
  "reach_reason": "not measured yet: this harness does not name the repository a session worked in, so a crossing cannot be traced",
  "started": "2026-09-14T13:00:00+00:00",
  "rhythm": [
    1,
    1
  ],
  "route": [],
  "trace_basis": "typed-turn order; Grok Bot export has no top-level event timestamps",
  "schema_version": 1
}
```

`samples/sample_grokbot_safe_real_shape.jsonl`:

```json
{
  "harness": "Grok Bot",
  "is_sample": true,
  "activity_label": "bot activity",
  "project": "session",
  "turns_typed": 7,
  "tool_calls": 7,
  "reach_reason": "not measured yet: this harness does not name the repository a session worked in, so a crossing cannot be traced",
  "started": "2026-09-14T15:00:00+00:00",
  "rhythm": [
    1,
    1,
    1,
    1,
    1,
    1,
    1
  ],
  "route": [],
  "trace_basis": "typed-turn order; Grok Bot export has no top-level event timestamps",
  "schema_version": 1
}
```

The helper also printed `private preview; not posted` and a localhost
`#import=` URL for each fixture. Those wrapper fields are intentionally omitted
above so the blocks reproduce only the `metrics` objects.

## Browser observations

Opened the second generated localhost import URL.

- The page said `Private by default`, labelled the card `not posted`, and
  explained: `This sample is for trying the preview. It cannot be saved or
  posted. Capture your own session to share a run.`
- Audience was unset. The select showed `Choose an audience`; no visibility
  option was preselected.
- The export-contents line was present:
  `This sample carries: the project folder name, counts, timing, the activity
  trace, a reach flag and reason, an activity label, route metadata. It never
  carries prompts, code or file paths. MCP names travel only if you tick the
  box below. Rig counts and notes are saved to your profile even when the run
  is Only me.`
- `Short caption` accepted temporary text. `Link to what was built (optional)`
  and the stack-notes input also accepted edits. No sign-in or Save action was
  attempted.
- The sample action was disabled and read `Sample — preview only`.

## Friction and clarity gaps

- Fresh Ubuntu setup needed an undocumented `python3.12-venv` system package.
  The failed first creation also left a `.venv` that setup could not repair
  after the package was installed.
- The imported generic project `session` produced the default title
  `session session`, which looks accidental to a stranger.
- The stack-notes control was an unlabeled input whose placeholder,
  `stack notes for friends (optional)`, did not explain what belongs there.
  This review adds a visible label and a concrete `Libraries, services or
  setup details` hint.
- `GROK-PUSH.md` is clear that preview is private and inert. A stranger still
  has to infer how to locate a real Grok JSONL export and how to know that an
  origin is the approved hosted origin. Links to the export procedure and the
  source of the approved origin would remove those two guesses.
- `HOSTED-CUTOVER.md` clearly separates Strava data from Grinder and is
  appropriately strict about writes. It assumes the operator already knows
  where Supabase exposed schemas and redirect URLs are configured, and it does
  not point from the deferred X/Origin sentence to the identity work that must
  precede enabling those paths.

## Claude identity lane prompt

```text
Implement the next Agentic Strava identity lane from the current reviewed
branch. Read AGENTS.md, PRODUCT.md, CONTRIBUTING.md, docs/HOSTED-CUTOVER.md and
the existing auth/profile code before editing.

Make GitHub and X linked Auth identities resolve to one Strava profile owned by
the authenticated Supabase user. Preserve github_handle as a compatibility
read/fallback for existing profile queries and URLs while making the Strava
profile's handle/display name provider-neutral.

After first sign-in, show Strava onboarding and create only the dedicated
Strava profile data. Do not write to Grinder public tables, functions, Auth
triggers or public-schema profiles. Add explicit cancelled-sign-in, provider
error and missing/empty identity states, preserving any private draft and a
clear route back.

Never merge accounts by handle, display name, email text from profile data or
other public metadata. Identity linking must use authenticated provider
identities and require a signed-in account flow; conflicts must stop with a
recoverable explanation rather than guessing.

Treat Origin as Cursor's code forge. Until an Origin OAuth application/provider
is registered and reviewed, do not add an Origin login button. Model Origin as
a post-sign-in repository connection with its own connect, cancel, error,
empty and disconnect states.

Keep capture → preview → post → browse intact and private by default. Add
focused tests for GitHub-only onboarding, GitHub+X linking to one stable Strava
profile id, github_handle compatibility, cancel/error recovery, rejected
handle-based merge, zero Grinder public writes, and Origin's post-sign-in-only
placement. Use disposable local data; do not deploy or run production SQL.
Run python3 scripts/dev.py check and browser-check the changed onboarding,
cancel and empty-state paths. Report local, tested, hosted and used separately.
```
