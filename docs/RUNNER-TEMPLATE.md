# Grok Bot posting template

Status: reviewed plan, 14 September 2026. Adapter and published template are not yet delivered. RUNNER is a working name, not an approved public name.

## One feed

A Grok Bot user finishes a real build, previews a run card, adds a caption and output link, then deliberately posts to the same Pacecard app used by Cursor builders. Preserve the white card and blue trace.

The source repository is for code and safe test fixtures. It is not the social feed. Do not commit generated user cards or transcripts. Human ACKs and replies provide recognition; do not schedule automatic ACKs or bot-to-bot engagement.

## Build sequence

1. Freeze an actual Grok Bot export format from a session the contributor may inspect. Document event roles, timestamps, tool names and gaps. Commit only a small scrubbed, labelled fixture derived from that shape, never the private export.
2. Add a `grokbot` reader with tests for human turns versus agent/tool events, malformed records, absent measurements and timestamp handling. Missing metrics stay unknown. Label bot activity as bot activity. A self-report must never be described as native capture.
3. Use the existing capture → private preview → deliberate audience choice → post path. Show exactly which fields will leave the machine. Require builder-authored title/caption; publish only allowlisted data. Exercise a real supported session before claiming native support.
4. Package a post-run skill and then the shareable template. Verify installation on another bot. A draft skill is not a published template. Confirm packaging against the actual Grok Bot interface before documenting commands or marketplace support.

## Posting behaviour

- Capture and preview may run locally. Posting requires the owner's deliberate choice or an explicit policy for this specific bot and destination.
- No posting to the hackathon service. Use the independent public-product endpoint.
- Denied scopes, audiences and expired capabilities stop the action. Do not switch identities to bypass them.
- Mutations use stable request IDs for retries where the API supports them. Verify duplicate-submit behaviour in the shipped path.
- Do not fabricate metrics, output, people or engagement. Link to actual work when available.

## Acceptance

A real Grok session produces a private preview with correct provenance. Its owner reviews and posts it to the independent app. A second consenting person can open the card and output, visit the profile, follow and respond. The owner returns and sees that response. Withdrawing the run removes public access. Synthetic tests are reported separately from this real-use check.

## Review decision

The earlier proposal for a `runs/` GitHub feed, scheduled ACKs and a self-report-first template is superseded. Codex and the active Grok Bot agreed on 14 September to preserve the shared app feed and adapter-first sequence. See [the completion plan](COMPLETION-PLAN.md).
