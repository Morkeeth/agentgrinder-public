# STRANGER-PASS · Agent Grinder

Cold-clone simulation — no Oscar credentials, no `~/.claude`, no Supabase keys.

**Run date:** 2026-09-02  
**Machine:** Ubuntu cloud agent VM (no local agent transcripts)

---

## Commands (exact)

```bash
tmpdir=$(mktemp -d) && cd "$tmpdir"
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
pip install -e . -q
python3 -m agentgrinder demo --no-open
bash scripts/pitch-demo.sh
```

**Verified on GitHub main** commit `e680bac` (2026-09-02).

---

## Step 1 · `pip install -e .`

```
WARNING: The script agentgrinder is installed in '/home/ubuntu/.local/bin' which is not on PATH.
```

**PASS** — installs without error (exit 0). PATH warning is cosmetic.

---

## Step 2 · `python3 -m agentgrinder demo --no-open`

```
  morkeeth · your-api — the retry-path refactor
  Claude Code · your-api · Sun 30 Aug 2026 · 06:00
      47 prompts |    2h 20m | 2:59 /prompt
  effort 213 tool calls · 12 files · 3 commits · 20.1/h

  card -> card.html
```

**PASS** — bundled sample renders; `card.html` created in cwd.

---

## Step 3 · `bash scripts/pitch-demo.sh`

```
(no local agent sessions — steps 2-5 use bundled sample)

=== AGENT GRINDER pitch demo ===

1/6 flex — your agents on this machine
No grinds found — run agentgrinder grind after a Claude or Cursor session.

2/6 vibe — meme label (no streaks)

  TOUCH GRASS
  You typed a lot. The agent barely moved. Operator mode.

3/6 roast — honest shape clowning

  ROAST SHAPE · TOUCH GRASS
  You typed a lot. The agent barely moved. Operator mode.

  · Shape: TOUCH GRASS. Nothing cruel to say — the numbers are mid.

4/6 grind card — latest session

  morkeeth · your-api — the retry-path refactor
  Claude Code · your-api · Sun 30 Aug 2026 · 06:00
      47 prompts |    2h 20m | 2:59 /prompt
  effort 213 tool calls · 12 files · 3 commits · 20.1/h

  card -> /tmp/pitch-grind.html

5/6 share card — claim-your-handle + vibe + roast

  share card -> /tmp/pitch-share.html
  screenshot it · the stub says claim your handle

6/6 rig card — stack for friends

  rig card -> /tmp/pitch-rig.html
  screenshot it · friends steal your stack
```

**PASS** — exit 0. Outputs `/tmp/pitch-grind.html`, `/tmp/pitch-share.html`, `/tmp/pitch-rig.html`.

---

## Step 4 · `bash scripts/seed-clean.sh /tmp/grinder-seed-test`

```
seed-clean OK: /tmp/grinder-seed-test (93 files)
exit: 0
```

**PASS** — Option A privacy pipeline clean.

---

## Summary

| Step | Result |
|------|--------|
| pip install | PASS |
| demo | PASS |
| pitch-demo | PASS (after sample fallback fix) |
| seed-clean | PASS |
| OAuth / publish | NOT TESTED — requires Oscar credentials |

**Overall: PASS** for local cold path without keys.

**FAIL on main before fix:** `pitch-demo.sh` exited 1 at step 2 (`vibe`: "no session found").
