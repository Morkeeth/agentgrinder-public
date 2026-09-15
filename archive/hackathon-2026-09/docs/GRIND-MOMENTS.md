# Grind moments · candidate product slice

The run already has counts, a share editor and returning practices. A moment connects those surfaces around one specific builder observation: select its pin, inspect the exact saved excerpt and limitation, make a reviewed card, then try one change against a frozen baseline.

## What is new

- Run detail offers an authored moment alongside its measured trace. The builder supplies a claim, evidence reference, exact excerpt, limitation and next action. A chosen activity bucket is explicitly an annotation, not a recovered timestamp. No existing note, transcript or local path is automatically copied.
- The saved moment is immutable and bound to the run's measurement revision. It inherits run audience rules, including revocation and exact-link access. Only the owner can add/remove a moment. Removing a moment does not delete the grind or an already-created practice.
- A selected moment fills the existing share studio with its claim, limitation and next action. The excerpt is not copied into the image/caption. Export requires explicit review; a clipped moment card cannot download. Private captions omit the run link. A stale or wrong-run moment cannot export against current measurements.
- One action creates a private practice and attempt together. The database locks and checks the exact run revision, freezes the baseline and makes identical retries idempotent. Changed retry input is rejected. Later-session selection, review, counts and incomparable outcomes reuse the existing practice flow.

## Meaning and limits

This is an authored observation and a reproducible link between product objects, not automatic evidence extraction, replay of raw agent events, an independent verifier or a causal improvement claim. An evidence URL is not fetched or certified. The current data can establish that a particular excerpt was saved; it cannot establish that the claim is true.

The current controlled fixture uses synthetic TEST DATA throughout. No real users, adoption, retention or hosted acceptance are claimed. The interaction retains the current shipped palette and the existing share renderer; this is not a new brand exercise.

## Deployment boundary

Apply `2026-09-06-moments.sql` after the existing ordered migrations and deploy `site/moments.js` with the updated site files. Nothing is deployed by these changes. If the table is unavailable, run details show a bounded unavailable message while the existing run/social/practice surfaces remain usable.

Moment fields share the run's present and future audience. The creation form requires explicit review of those fields. Database policy is the authority; hiding a form is not authorization. No notifications, external invitations, AI calls or automatic uploads are added.

## Verification

With Node22+ and installed project dependencies:

- `node scripts/test-database.mjs`: actual ordered PostgreSQL/PGlite migrations and role policies, plus moment → private practice → frozen baseline → later result. Includes ownership, public-to-private revocation, immutable text, changed-revision refusal, duplicate retry, foreign owner denial and preservation after moment removal.
- `python3 scripts/check-moment-fixtures.py`: isolated Chromium, controlled data/response fixtures, actual new and existing frontend modules. Tests save failure/retry, escaped excerpt, trace pin, explicit review, PNG bytes, stale export refusal, practice navigation and later review. Screenshots are synthetic, not hosted proof.
- `python3 -m pytest -q tests/test_browser_contract.py tests/test_progress_fixture_contract.py tests/test_run_contract.py tests/test_privacy_promises.py`.

Remaining: fresh review of this candidate, full routed authenticated hosted client after approved deployment, and whether a real builder finds this moment worth sharing or returns to the practice. Mechanical completion does not settle those product questions.

## The stranger's path · 2026-09-07

A moment could be read by anyone who could read the grind, but only its author could act on it. A reader who was not there got a link to a generic practice list, so the technique and its evidence were dropped on the floor at the exact point someone wanted to try it.

- Any reader of a readable grind can now keep the moment's next practice on their own account. The gate is readability, not ownership (`grinder_adopt_moment`, `2026-09-07-adopt.sql`).
- The frozen baseline is one of the **reader's own** measured grinds, chosen by them. `grinder_run_snapshot` refuses any run they do not own, so the author's numbers can never become someone else's baseline.
- Keeping is an explicit consented act: an expected result, a chosen baseline and a ticked box. Nothing is sent to the author, nothing is written to their grind and no notification is raised.
- The kept practice records provenance as references only: moment id, source grind id and the moment's bound measurement revision. No title, claim or excerpt is copied, so an audience change is honoured. When the source stops resolving the practice page says so and the reader's own baseline, review and outcome stay.
- An older source measurement is labelled, not refused. That gate protects the author's own baseline binding; it is not a reason a reader cannot try the technique.
- The practice page shows where the practice came from and states that the source builder's counts are not shown. The only comparison rendered is the reader's own baseline against their own later session, with unknown values rendered as Unknown, and it is labelled as not establishing that the practice caused the difference.

### Limits

Two attempts by the same person are still two observations, not a controlled result. Nothing here is uploaded, published or shared outward; the reader's practice is private by default and the author is never told. No real builder has used this path; the checks below are controlled fixtures.

Verification adds: the stranger block in `scripts/test-database.mjs` (private source refused, anonymous refused, own baseline enforced, author grind untouched, provenance private to the adopter, stale source recorded, idempotent keep, later review, audience revocation survivable), the stranger journey in `scripts/check-moment-fixtures.py`, and `python3 -m pytest -q tests/test_stranger_practice.py`.
