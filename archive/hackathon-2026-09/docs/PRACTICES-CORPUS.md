# AGENT GRINDER — practices corpus (cited, for the coach)

Documented best-practices from top agentic engineers. This is the material the coach's grounded
recommendations draw on. Agent Science discipline: each carries a source; **verify any figure at the
primary source before quoting it publicly** (search snippets are a lead, not proof).

## The practitioners + what they document
| Practitioner | Practice (claim) | Source | Verify |
|---|---|---|---|
| **Andrej Karpathy** | A `CLAUDE.md` rules file cut agent mistakes ~41%→11%; ~80% agent / 20% human; one task per session | aibuilderclub.com/blog/karpathy-claude-md-rules | figure at source |
| **Simon Willison** | "Agentic Engineering Patterns" guide; the **explore → plan → code → commit** loop; scope tasks tightly (name the file, the scenario, how it's tested); the skill is **describing "done" precisely** | simonwillison.net/2026/Feb/23/agentic-engineering-patterns | quotes at source |
| **Geoffrey Huntley** | The **"Ralph" loop**: fresh agent, clean context, **one unit of work, commit, exit**; documented rules enable self-correction | linearb.io/blog/ralph-loop-agentic-engineering-geoffrey-huntley | ✓ concept solid |
| **Thorsten Ball** | An agent is "an LLM, a loop, and enough tokens"; **make the check real, define when to stop** | ampcode.com/how-to-build-an-agent | ✓ |
| **Addy Osmani** | Self-improving agents: rules/memory that evolve from mistakes | addyosmani.com/blog/self-improving-agents | ✓ |
| **Research (arXiv)** | "Professional developers **don't vibe, they control**" (2512.14012); "Agentic Software Engineering: foundational pillars" (2509.06216) | arxiv.org | peer-reviewed-ish, cite id |
| **Anthropic (official)** | **Context is the key resource** — `/clear` between tasks, Explore→Plan→Implement, plan mode + `CLAUDE.md` + TDD; they cut 80% of Claude Code's system prompt with no eval loss | anthropic.com/engineering/effective-context-engineering-for-ai-agents | ✓ primary source |
| **Mitchell Hashimoto** | **Always have an agent running** ("if I'm coding, an agent's planning; if they're coding, I'm reviewing"); research + plan first, save to **spec.md**; consult a read-only "oracle" subagent; run parallel models when confidence is low | newsletter.pragmaticengineer.com/p/mitchell-hashimoto ; simonwillison.net/2026/Feb/5 | ✓ |
| **CodeScene** | Agentic coding needs **more** rigor/structure/quality, not less | codescene.com/blog/agentic-ai-coding-best-practice-patterns | ✓ |

## The through-line (what they all agree on)
1. **A real check / verification loop is the whole craft** (Ball, Huntley, Willison, the arXiv "control" paper). Activity without a verified result is not the work.
2. **Rules/context files matter** (Karpathy, Osmani) — the highest-ROI, cheapest fix.
3. **Commit per unit of work** (Huntley, Willison's explore-plan-code-commit).
4. **Scope tightly; define "done"** (Willison, single-task sessions).
5. **Control, not vibe** (arXiv 2512.14012) — the science backing for the whole product's stance.
6. **Context is the resource** (Anthropic) — clear between tasks; plan before coding.
7. **Plan first, save the spec** (Hashimoto, Willison) — a written plan/spec.md before the agent runs.

## Map: practice → detectable characteristic → coach line
| Practice | Can AG detect it? | Coach recommendation |
|---|---|---|
| Rules file present | YES (local: CLAUDE.md/.cursor/rules) | "no rules file — Karpathy: ~41%→11%" |
| Commit per unit of work | YES (commits vs tool activity) | "N tool calls, 0 commits — commit per unit (Huntley/Willison)" |
| Verification real | PARTIAL (ship flag, commits) | "activity high, nothing shipped — make the check real (Ball)" |
| Tight scope / one objective | PARTIAL (regions touched) | "session spanned K regions — one bounded objective (Willison)" |
| Plan/spec file present | YES (local: spec.md/PLAN.md) | "no plan/spec in this project - plan first, save spec.md (Hashimoto/Willison)" |
| Self-improving rules | FUTURE (rules-file churn over time) | later |

## Honest note
We cite *documented public practice*, never a practitioner's private session metrics (those don't
exist publicly). The coach applies these to characteristics we can actually detect in *your* session.
