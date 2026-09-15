# September 14 entry readiness

Agent Grinder is the single entry. MAGNET remains the disclosed engine library. The closed Strands ruling is unchanged.

Official source checked September 10: https://agentsforhumans.devpost.com/rules and https://agentsforhumans.devpost.com/details/dates . Deadline September 14, 17:00 PDT = September 15, 02:00 CEST. The build period starts August 10. Strands is required; AgentCore is optional. Submit an English description, public MIT/Apache repository with README and architecture diagram, public YouTube/Vimeo video up to five minutes, and AWS Builder ID. Provide a working test path free through judging. Disclose incorporated prior work. Eligibility includes adult entrants and listed geographic/employment exclusions; Sweden is not listed as excluded. This is a requirements check, not a new eligibility ruling.

## Achieved locally

- Existing stranger practice build integrated from `ced62230cd2a6e2a9715f5cc7fa9d01a1918ee70` onto September 10 main base `a3ea01c`.
- Authored moment → reviewed share export → private practice with frozen baseline → later run → recorded review.
- Reader keeps a readable moment’s practice on their own baseline. Source access can be revoked without deleting their review.
- Changed-baseline retry is refused, rather than returning an old attempt as though the new choice were saved.
- Browser checks use controlled responses. PGlite executes the real migrations and access rules. These are not independent users or a hosted acceptance run.
- Grinder coach: actual Strands dispatch with a scripted local provider on the bundled sample. Inflated verdict refused. No Bedrock invocation in this pass.

## Release boundary, probed

September 10 live reads returned HTTP 404 for `/moments.js`; `grinder_run_moments` and `grinder_adopted_moments` returned PGRST205. Practice version and attempt tables returned HTTP 200 for zero-row schema reads. Existing hosted run-query/access checks pass; that does not prove this new journey is deployed.

No deployment, remote push, account change, paid provider call, or submission was performed. The original repositories’ dirty `hack.md` files are preserved.

## Execute next, in order

1. Root reviews the isolated candidate and local evidence, then integrates the accepted commit without overwriting human work.
2. With release authority, apply missing migrations in `scripts/migration-order.txt`, deploy the matching frontend, and test the authenticated reader → own baseline → later run → return path against the hosted database. Include another role and revoked source access.
3. Bind submission claims and testing instructions to that final revision. The architecture is in `docs/architecture.md`; the revised product description is `docs/DEVPOST-DESCRIPTION.md`. Do not use the old readiness assertions as current evidence.
4. Complete the event form’s account and public-media fields when the operator chooses the submission step. Confirm receipt separately from draft readiness.

No missing primary-value dictation is inferred as a microphone feature request. Current product direction remains record, flex, improve. FAVOUR is nonblocking and was not touched.

## Reproduce without new spend

Use Python 3.12 with the existing Strands extra, Node 22, and installed project dependencies.

```sh
python3 -m pytest -q
node scripts/test-database.mjs
python3 scripts/check-moment-fixtures.py
python3 -m agentgrinder coach samples/sample_session.jsonl --model local --json
python3 scripts/show-refusal.py
python3 scripts/check-hosted.py
```

The browser script generates explicitly labelled test screenshots. Do not use them as independent-user evidence. The one skipped Python calibration test requires a second real harness transcript.
