# Judge path · Agent Grinder (under five minutes)

This is the product path a stranger can complete without a walkthrough.

Production: [agentgrinder.vercel.app](https://agentgrinder.vercel.app). Run-focused runtime `469ef1f` was promoted on September 14 as `dpl_7h5nf54mvChzJA9kYd6U2o1iGCKs`; production bytes matched the reviewed candidate. Earlier in this release pass, database migrations, GitHub sign-in and a real hosted private TEST practice were exercised. The two-builder persistence evidence below is from disposable test accounts, not independent users.

## What to open

Open [the bundled example](https://agentgrinder.vercel.app/?example) on a phone-width window or desktop. No account or payment is needed.

For a local copy, from the repo root:

```bash
python3 -m http.server 8765 --directory site
```

Then open `http://127.0.0.1:8765/?example`.

Label: **BUNDLED EXAMPLE · public-safe fixture**. Not live users. Not a live language model.

The bundled example (`site/example.js`) is labelled onboarding only. Persistence, adoption and revocation are the real moments/practices RPCs, exercised in an isolated disposable Postgres.

## The five-minute loop

1. **Landing** (`/`). A real run card leads the page. *Post your first run* opens onboarding; *Try a sample run first* opens the labelled example. Capture is local and import starts private. No account is needed to read the public card or example.
2. **Example** (`/?example`). A deterministic Strands/tool sequence (recorded) finds a **named** friction: `test_draft_renders` was claimed without evidence in that turn. Consequence and one experiment are visible. Mode banner says this is **not autonomous reasoning**.
3. Accept or edit the experiment. Freeze the fixture sitting as baseline.
4. Return with the later labelled sitting. Keep / change / drop / incomparable. Original measurements remain. One observed outcome, not a score-as-proof.
5. Author a moment. Tick the review box. Switch to **another builder (fixture role)** — their own baseline, not the author's counts. Return, save an outcome, optional PNG/caption review (`/?example=share`).
6. **Persisted APIs (disposable, not production):**

```bash
# From a clone of the public repository; Node 20+ and Python 3.12.
npm ci
python3.12 -m venv .venv
.venv/bin/pip install -e ".[coach]" playwright
.venv/bin/python -m playwright install chromium
npm run test:journey
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/check-persisted-journey.py
```

Screenshots and the receipt are saved to a new temporary directory printed at startup. Set `GRINDER_JOURNEY_RECEIPTS` to choose your own output directory.

Two authenticated TEST DATA contexts hit the real `grinder_start_attempt` / `grinder_review_attempt` / `grinder_adopt_moment` RPCs. Coach → accept/edit on the same card → freeze own baseline → later run and review → deliberate share → second builder adopts onto **their** baseline → their outcome → revocation leaves owned work. Different harnesses with claim counts do not get a green comparable badge.

7. **Live model (optional, your machine only):**

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[coach]"
.venv/bin/agentgrinder coach --live-status
```

If AWS/Bedrock is missing, that command prints the **exact** missing item and does not invent a live review. Do not spend against a paid provider for this judgement.

Bring-your-own: `python3 -m agentgrinder grind` then `grind --push`. Import audience defaults to **private**. Coach text is metrics-only: directory paths are stripped before import, cards, JSON and push.

## What success looks like

- A stranger gets the promised value without an explanation.
- Demo and live modes cannot be confused.
- A second builder's attempt sits on **their** freeze, and revocation language is on the return.
- Feed → run → discussion is the main public path. Saved practices open under “One practice for your next run”. Existing Community, Crew and challenge routes are outside launch navigation.

## What this is not

Independent real-world adoption or a hosted two-builder acceptance claim. A live Bedrock receipt remains pending. Private transcripts do not belong in Git or in the cloud preview. The disposable PGlite journey is TEST DATA, not live users.
