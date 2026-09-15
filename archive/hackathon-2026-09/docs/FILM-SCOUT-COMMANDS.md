# FILM-SCOUT-COMMANDS · copy-paste for Oscar

Film tomorrow — run from repo root on a machine with real Claude/Cursor sessions for best results.
Without sessions, `pitch-demo.sh` falls back to bundled sample (still renders cards).

---

## Terminal WOW (2 min arc)

```bash
# 0. setup (once)
cd ~/path/to/agentgrinder
pip install -e .

# 1. flex — three agents on one machine
agentgrinder flex

# 2. grind — the signature card (real session)
agentgrinder grind --harness auto --no-rank -o /tmp/film-grind.html
open /tmp/film-grind.html   # macOS; xdg-open on Linux

# 3. share — claim + vibe + roast (screenshot this)
agentgrinder share --claim --vibe --roast --no-open -o /tmp/film-share.html
open /tmp/film-share.html

# 4. rig — stack card for friends
agentgrinder rig --share-names --no-open -o /tmp/film-rig.html
open /tmp/film-rig.html

# 5. optional heist
agentgrinder heist YOUR_HANDLE --thief FRIEND_HANDLE -o /tmp/film-heist.html
open /tmp/film-heist.html
```

**No sessions?** Full scripted path still works:

```bash
bash scripts/pitch-demo.sh
open /tmp/pitch-grind.html /tmp/pitch-share.html /tmp/pitch-rig.html
```

---

## Web WOW (browser)

| URL | What to show |
|-----|--------------|
| https://agentgrinder.vercel.app/?pitch | 10-second legibility: "agents propose, humans publish" |
| https://agentgrinder.vercel.app/?event=agents-for-humans | Sep 14 event page |
| https://agentgrinder.vercel.app/?claim=1 | Viral claim-your-handle stub |
| https://agentgrinder.vercel.app/?onboard=agent | A2A/MCP agent onboarding (anti-Moltbook gate) |
| https://agentgrinder.vercel.app/?explore | Public feed (needs published grinds) |

---

## Publish arc (Oscar credentials only)

```bash
agentgrinder login                    # GitHub OAuth — needs Supabase redirect URLs configured
agentgrinder grind --harness auto --push
# browser opens import URL → sign in → publish → copy run URL for feed shot
```

---

## Sound bites (say while filming)

- "Where you post your real runs."
- "Every number traces to the session log."
- "Agents propose. Humans publish."
- "No Moltbook. No streaks. No ghost metrics."

---

## Shot list

| Shot | Source |
|------|--------|
| Terminal flex output | `agentgrinder flex` |
| Grind card close-up | `/tmp/film-grind.html` or `docs/shots/six/tonight-light.png` |
| Share card with vibe | `/tmp/film-share.html` |
| Rig card | `/tmp/film-rig.html` |
| Pitch page | `/?pitch` |
| ACK tap | `/?explore` → open run → ACK |
