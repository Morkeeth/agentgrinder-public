# Release notes · complete focused journey (2026-09-13)

Stacked on candidate `day/2026-09-11-grinder-ambition` @ `be5704c`. PR1 remains the release candidate. This work is an isolated branch. Coordinator owns production deploy and final submission.

## Built

- Stranger landing with one start action, the signature *I tried this. Show me what changed.*, and a labelled bundled example that needs no account.
- Bring-your-own capture stays private by default, with concise local import copy and evidence-availability language (dashes name what was not measured).
- Strands coach still checks every claim and file, then proposes **one** supported friction with tool evidence and **one** next-session experiment. Scripted/demo vs Bedrock/live labels are printed. `agentgrinder coach --live-status` returns exact missing configuration and will not start a fake live run.
- Coaching-to-practice: accept/edit the experiment on a measured grind, freeze that grind as baseline, return with keep/change/drop/incomparable, original measurements preserved, one observed outcome required.
- Bundled example continues through moment review, a second-builder fixture role on **their** baseline, and outcome export using the existing share studio.
- Community overview leads with public techniques (honest empty state if none). Returning builders land on pending practices and recognition, not a marketing page.
- Forward migration `2026-09-13-coach-mode.sql` (nullable `runs.coach_mode`) and `2026-09-13-comparable-sittings.sql` (keep/change/drop requires matching harness **and** time basis). Not applied to production here.
- Practice review UI and return-view export refuse a green comparable badge when harness or `trace_basis` differs, even if claim counts are present on both sittings.
- Coach `named_targets` no longer extracts directory paths from claim text. Export, import, HTML cards, JSON dumps and push replace path-shaped tokens. Local coaching still names `test_*` identifiers and slash-free basenames.
- Real two-builder persistence (coach freeze → later review → share → adopt onto the reader's baseline → their outcome → revocation) is exercised in isolated PGlite with distinct JWTs, not `example.js` sessionStorage. `site/example.js` stays labelled onboarding.

Preserved: existing moment authoring, adoption RPC, outcome export, practice RLS, nav (Feed / My runs / Community / Inbox).

## Tested

- Unit: 276 passed (`tests/` minus `test_claim_rule.py`); one pre-existing Cursor/Codex `claims` key assertion in `test_coach_degrade.py` is unchanged from the candidate.
- Path leak: synthetic `/Users/…/secret-plan.md`, `~/private/keys.env` and `C:\Users\…` are absent from named_targets, export_run, solocard, render, JSON dumps and import `rejectPaths`. `test_draft_renders` remains the supported experiment.
- Comparable sittings: UI badge, return-view HTML, and `grinder_review_attempt` refuse keep/green comparable when harness or `trace_basis` differs even with non-null claim counts.
- Database: ordered PGlite migrations including `2026-09-13-comparable-sittings.sql`, plus existing moment/adopt/revocation checks.
- Persisted journey: `npm run test:journey` and `python3 scripts/check-persisted-journey.py` — two JWT contexts, real RPCs, disposable PGlite, labelled TEST DATA. Not production.
- Browser: bundled example phone+desktop; practice discovery plus harness-mismatch badge; persisted coach→adopt→revoke at 390 and 1280.
- Not claimed: hosted auth against production, live Bedrock execution, independent human adoption, a Vercel preview on this PR (none attached at push time).

## Hosted

- Not deployed by this agent. Root `main` and agentgrinder.vercel.app are not assumed to contain this candidate.
- Preview: whatever Vercel/GitHub attach to this branch. Bundled example is static (`site/bundled-example.json`, `site/example.js`) and does not need the moments/adopt DDL.
- Moments, adoption, and `coach_mode` on stored runs need the coordinator to apply the listed migrations in `scripts/migration-order.txt`.

## Used

- Bundled public-safe fixture derived from `samples/sample_session.jsonl` via the real coach tools (deterministic mode).
- No private transcripts, credentials, or production writes.
- No new paid-provider spend.
