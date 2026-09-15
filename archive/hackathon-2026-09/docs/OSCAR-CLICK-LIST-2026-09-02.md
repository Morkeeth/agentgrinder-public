# OSCAR-CLICK-LIST · 2026-09-02

**Oscar only.** Cloud agent prepared these; does not execute outward acts.

---

## 1. Supabase OAuth redirect URLs

Project: `xengine-review` (schema `agentgrinder`)

Add to Supabase Auth → URL Configuration:

| URL | Purpose |
|-----|---------|
| `https://agentgrinder.vercel.app` | Production site |
| `https://agentgrinder.vercel.app/` | Trailing slash variant |
| `http://localhost:3000` | Local web dev (if used) |

GitHub OAuth provider must be enabled with correct callback.

**Verify:** `agentgrinder login` on Oscar's machine → completes without redirect error.

---

## 2. Vercel redeploy

If `site/` or `vercel.json` changed since last deploy:

1. Push to `main`
2. Vercel dashboard → agentgrinder → Redeploy (or auto on push)
3. Confirm `https://agentgrinder.vercel.app/?pitch` loads

---

## 3. Devpost register / submit

**Do not submit until Strands Agents ruling** (see `docs/MOONSHOT-MEMO-2026-09-02.md` OPEN QUESTIONS).

When ready:

1. https://agentsforhumans.devpost.com/ → Join Hackathon
2. Submission fields from `docs/DEVPOST-READY.md`
3. Upload 3 screenshots from `docs/shots/`
4. Record 5-min demo video (script in DEVPOST-READY)
5. Public repo: https://github.com/Morkeeth/agentgrinder
6. Optional: builder.aws blog post for +0.6 bonus

---

## 4. Stranger recruit — one friend DM template

```
Hey — I'm entering Agent Grinder in the Agents for Humans hackathon (Sep 14).
It's "Strava for coding-agent sessions" — one command after Claude/Cursor turns
your session into a shareable card (metrics only, no prompt text).

Would you cold-run this and tell me honestly if you'd post the card?

git clone https://github.com/Morkeeth/agentgrinder.git
cd agentgrinder && pip install -e .
python3 -m agentgrinder demo
bash scripts/pitch-demo.sh

No account, no keys. Takes ~2 min. Brutal honesty welcome.
```

---

## 5. PNG eyeball

Before Devpost submit, open each file in `docs/shots/` at real size — OCR not run (UNSCANNED per seed-clean audit).

---

## 6. Strands Agents SDK (blocking)

Decide before submit:

- [ ] Add thin Strands wrapper and document in README
- [ ] Skip Devpost; launch PH / stranger gate separately
- [ ] Ask organizer via forum

Cloud agent does **not** implement Strands without ruling.
