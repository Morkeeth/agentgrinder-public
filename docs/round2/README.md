# Round 2 review receipts

Independent review lane: `codex/strava-review-round2-20260914`.

- Canonical findings with exact reproduction: also written to
  `/Users/morkeeth/.local/state/day-run/2026-09-14/restart-2030/REVIEW-ROUND2.md`
  for the integration lane to consume.
- Copy in this folder: `REVIEW-ROUND2.md` (same body).
- Original PR11/PR12 `RETURN.md` files were not overwritten; they stay in their worktrees
  and under integration `docs/round2/*-RETURN.md`.

## Fixes offered to integration (separate commits on this branch)

1. **R2-01** Exact reply deep-link: resolve by reply id, page until focused, only then show removed.
2. **R2-02** Notification read marking: confirm updated ids, reset marks on recipient change,
   disconnect inbox IntersectionObserver on remount.

Evidence class: local disposable / source inspection. Not hosted OAuth. Not consenting users.
