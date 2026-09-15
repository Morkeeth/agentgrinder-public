# Stranger audit: can Oscar send this to his friends today?

*4 September 2026. Run as a cold clone of what is actually published, not as a review of the
working tree.*

**The stranger:** a technical friend of Oscar's. They click a link or clone a repo, form an
opinion in about ten seconds, and never say why they closed the tab. Two paths, both checked: the
person who clicks the live URL, and the person who clones and runs.

**The machine, stated because a timing without one is not a measurement:** MacBookPro18,3, arm64,
macOS 26.6.2, system Python 3.12.5, warm network and warm DNS. Cold clone into an empty scratch
directory, `env -i` with an empty `HOME`, no credentials, no ambient packages on the path.

**The object under test:** `origin/main` at `60a0c49`. That is what a friend gets. The six commits
this lane made today are **not pushed**, and that fact produces the first two findings rather than
being a footnote to them.

---

## VERDICT

**Not sendable today.** Three blockers, and the first one is the reason the other findings are as
bad as they are. None of the three is a bug in the code. Two are a merge, one is a ruling.

The good news is that everything a friend *does* reach works. No command produced a traceback, the
cold clone is genuinely one command with no dependencies, the site is up and honest, and no secret
exists anywhere in the history.

---

## BLOCKERS

### B1. Everything fixed today is invisible to a friend

**Promised:** the repository is the product, so what the docs say is what a stranger gets.
**Happened:** `git clone` lands on `main` at `60a0c49`. The lane branch
`lane/claim-rule-population-2026-09-04` at `81029d9` is on no remote:
`git branch -r --contains 81029d9` returns nothing. So a friend cloning right now gets the
pre-audit code *and* the pre-audit docs, including the surfaces that were measurably wrong.
**Fix:** merge the lane branch to `main` and push, before the link goes to anybody.

### B2. A Cursor friend is told something false, by the tool, to their face

**Promised:** `--harness cursor` reads a Cursor session and cards it.
**Happened:** on published `main`, with a Cursor transcript containing two `Write`/`StrReplace`
blocks carrying absolute paths and a `Shell` command containing `git commit`, the tool prints:

```
  Cursor transcripts carry no file paths and no commits, so the grind trace
  cannot be drawn for them. The v1 card is rendered instead
```

Both halves of that sentence are false, and the file it just read is the disproof. The card comes
out with dashes for files touched, commits, artifacts produced and reach. A friend on Cursor is
told their harness is the limitation when the reader was.
**Fix:** B1. The lane branch already reads all four; on it the same fixture cards 2 files, 1
artifact and 1 commit.

### B3. A friend cannot post a run without a GitHub account, and the door is not built

**Promised:** "Where you post your real runs", and a README that opens "no account".
**Happened:** the local card genuinely needs no account. Publishing does. The site's only sign-in
is `signInWithOAuth({provider:'github'})`, twice, no alternative. And the anonymous door does not
exist yet: an anonymous insert against the live database returns

```
HTTP 401  {"code":"42501","message":"new row violates row-level security policy for table \"runs\""}
```

Probed with a duplicate primary key so no row could be created either way; the row count was 2
before and 2 after. That is the *correct* state, there is no open write policy, but it means every
friend who wants to publish needs GitHub and an OAuth authorisation.
**Fix:** ruling R3, the rate-limited edge function. Until then the link is "look at Oscar's runs",
not "post yours".

---

## THE RULING THAT GATES THE SEND

**R5 is unruled and it blocks the walkthrough.** `docs/WALKTHROUGH.md` quotes a headline figure.
Oscar has not chosen which one it is.

> Keep **0.63** as the headline with the Claude Code 0.72 printed beside it, or promote **0.72**
> with 0.63 kept as the corpus-wide note?

**Recommendation: keep 0.63.** The reason is not conservatism. It is that raising your own
published score on your own authority is not something this project gets to do quietly, and that
sentence is the product. The walkthrough is written that way; if he rules the other way, one
section changes.

**R1 and R2 change shape for this audience.** For a judge, `uvx agentgrinder grind` and a real
domain were nice. For a friend who was sent a link, they are the difference between trying it and
closing the tab: today the install is a clone into a directory they did not ask for, and the URL is
a `.vercel.app`. Both remain his click and his card.

---

## COSMETIC

### C1. `authorship` prints a green OK over a population of zero

On an empty machine it exits 0 and prints `parts sum to the total: 0 + 0 + 0 + 0 + 0 = 0  OK`.
A check that says OK about nothing is the exact failure class this product exists to name, printed
by the product. **Fix:** say "no records to check" and skip the sum line when the total is 0.

### C2. `history` prints five empty headings

It honestly opens `0 grinds on this machine`, then prints five section headers with nothing under
them. Harmless, reads like a bug. **Fix:** print the first line and stop when there are 0 grinds.

### C3. Two commands dead-end where the best one does not

`grind` with no data is the best message in the tool: it names all four search paths and points at
`demo`. `vibe` and `roast` print `no session found` and stop, with no path and no next step.
**Fix:** reuse `grind`'s message.

### C4. `rig` on an empty machine builds a share card that says nothing

Exit 0, writes `rig.html`, a 1200x630 card reading `@you · 0 MCPs · 0 skills · Harness: run a grind
to detect harness` under the heading "SHOW YOUR RIG", and invites the reader to "Steal this rig".
Nothing is false. It is an empty poster asking to be shared. **Fix:** tell them to run a grind
first, rather than handing them the poster.

### C5. Hackathon furniture on the page being sent to friends

The live nav carries `Sep 14` and `Pitch`. A friend does not know what Sep 14 is, and after Sep 14
it is stale on a page Oscar is still sending to people. **Fix:** his call, but the deadline badge
should come down when the audience changes.

---

## WHAT HELD, named so that "clean" means something

- **Cold clone is genuinely one command.** 1.18 s real, 16 MB, 143 files, lands on `main`, warm
  network on the machine named above. No install step is needed to reach a card.
- **The "no dependencies" claim is true.** `python3 -X importtime -m agentgrinder demo` under
  `env -i` imports nothing outside the standard library. No `strands`, no `requests`, no `boto`.
- **`demo` works cold**, exit 0, 0.64 s, with an empty `HOME` and no network.
- **The empty-machine message is the best thing in the CLI.** `grind` with nothing to read names
  all four transcript locations it searched and points at `demo`. Exit 1, no traceback.
- **No command produced a traceback.** `demo`, `grind`, `grind --list`, `grind --harness auto`,
  `history`, `authorship`, `share`, `flex`, `vibe`, `roast`, `rig` all ran cold and degraded with a
  sentence. `profile` and `privacycheck` print argparse usage and exit 2, which is a CLI behaving.
- **No secret anywhere in the full history.** `git log --all -p` scanned for service-role keys,
  JWTs, AWS keys, GitHub tokens and OpenAI keys. One `eyJ` hit, and it decodes to `{"harness":"`,
  a base64 run payload in a share URL, not a token. The only credential in the tree is the
  publishable Supabase key, which is the one that is meant to be public.
- **No open write policy.** Anonymous inserts are denied on both `runs` and `profiles`.
- **The live site is up and fast.** `/` 200 in 0.15 s, `/methodology` 200, the run permalink 200.
- **A logged-out friend sees a real card immediately.** `FEATURED_SNAPSHOT` ships inside the page
  with 7 claims, 3 verified and 37 coach tool calls on a real Claude Code sitting, so the argument
  of the product is on screen before any sign-in.

---

## Addendum: what has been fixed since this audit ran

*Appended after the findings, not folded into them. The findings above describe `60a0c49` and are
left exactly as they were recorded, because an audit edited to match the fix is no longer evidence
of anything.*

**C1, C2 and C3 are closed** on the lane branch, and each is held by a test.

- `authorship` on an empty window now says there is nothing to check and stops, instead of printing
  a table of zeros and a green OK. A second test asserts the sum still prints when there IS a
  population, so the check was watched going both ways rather than only silenced.
- `history` prints its honest `0 grinds` line and stops, instead of five empty section headings.
- `vibe` and `roast` now print `no_session_message()`, the same text `grind` uses: every path
  searched, and `demo` as the next step. The helper already existed; they were not calling it.

Verified cold afterwards under `env -i` with an empty `HOME`, the same conditions the findings were
collected under.

One note on the tests, because it is the same lesson as the audit itself. The first version of the
`authorship` test faked `HOME` by monkeypatching `os.path.expanduser`. It passed alone and failed
in the suite: by the time it ran, other tests had already imported the modules that resolve those
paths, so the real machine's 354 records walked into a test about an empty machine. It now drives
the branch directly. A test whose result depends on which tests ran before it is not measuring what
it claims to measure.

**C4 and C5 are open and are not this lane's to close.** C4 changes what a share command produces,
and C5 is a decision about what the site says to an audience that just changed from judges to
Oscar's friends. Both are his.

**B1, B2 and B3 are untouched**, because two are a merge and one is a ruling.

## Addendum 2: re-run on the merged result, and one finding this audit missed

*The audit above describes `60a0c49`. The lane branch was merged into `main` locally at `76fc2a0`
on Oscar's ruling, which is exactly the moment the audit's own last line applies. Re-run as a cold
clone of the merged tree, `env -i`, empty `HOME`. 148 tracked files, 174 tests pass.*

### B2 is closed in the tree, checked with the same fixture

The Cursor fixture that produced the false sentence was run again against the merged clone. Same
transcript, same command, before and after:

- **60a0c49:** `"Cursor transcripts carry no file paths and no commits, so the grind trace cannot
  be drawn for them."` The produced over promised cell read a dash on both sides.
- **76fc2a0:** `"files, commits and reach are read from the transcript. The grind trace is not
  drawn: Cursor stamps a time on typed turns only."` The same cell now reads 1 over a dash.

The sentence a friend is told is true, and it names what is genuinely missing rather than blaming
their harness. C1, C2 and C3 also verified closed on the merged clone: `authorship` says "nothing
to check", `history` says "Nothing to rank yet", `vibe` names every path searched, `demo` still
works cold. No traceback from any of them. `scripts/claim-calibration-report.py` exits 1 with the
cursor stratum named, which is the intended state.

### B1 is NOT closed, and the merge did not close it

`main` is nine commits ahead of `origin/main`. Nothing has been pushed and nothing has been
deployed, because neither was asked for and both are separate acts. **A friend cloning the public
repository right now still gets `60a0c49`, and is still told the false sentence.** A local merge
changes what is true in this working copy, not what is true for a stranger.

### B4, NEW AND THE MOST SERIOUS THING IN THIS DOCUMENT: a private project map is in the public repo

Found by a review panel, not by this audit, and verified here at the published object.

**Promised:** the public nightrun card redacts repository and lane names.
**Happened:** the redactor works, and the un-redacted original was committed beside its own
redacted output. Both are tracked and both are on `origin/main` today.

| file, on `origin/main` | size | private project names |
|---|---|---|
| `nightrun-public.html` | 102,457 b | **0**, with 350 `repo N` labels in their place |
| `nightrun.html` | 104,247 b | **115**, across five names, counted per name and not reproduced here |

Neither file is served by the website; `vercel.json` publishes `site/` and both of these sit at the
repository root. So the exposure is the public GitHub repository, not the live URL. It is still a
**one-way door that is already open**: the file is in every clone and fork made since it was
committed.

**Fix, as first written:** Oscar's, because removing it from the published history needs a rewrite
and a force push,
which are his acts and not reversible by anyone else. Deleting the file at `HEAD` does not remove
it from the log.

**And why this audit did not find it.** The privacy check above scanned the full history for
service-role keys, JWTs, AWS keys, GitHub tokens and OpenAI keys, and reported clean. That result
was correct and it was about the wrong object. The leak is not a credential, it is a map of what
Oscar is working on, sitting in a 104 KB HTML file next to the redacted copy that proves somebody
already knew it needed redacting. A privacy check that only knows the shape of a secret cannot see
a secret with a different shape.

## Addendum 3: B4 was priced, and the price is not what either option assumed

*Oscar ruled: fix it, and the repository stays public for the hackathon. That rules out making it
private and leaves deleting at HEAD or rewriting history. Measured before recommending, because the
fact that decides between them was not in anyone's hands.*

### The measurements

| fact | value | how |
|---|---|---|
| forks of `Morkeeth/agentgrinder` | **0** | `gh repo view --json forkCount`, and `gh api .../forks` returns 0 |
| stars | 0 | same call |
| public since | 31 Aug 2026, four days | `createdAt` |
| Wayback snapshot | **none** | `archive.org/wayback/available`, empty `archived_snapshots` |
| commits touching `nightrun.html` | **1**, the initial public seed | `git log -- nightrun.html` |
| anything worse than names inside it | **none**: 0 absolute paths, 0 emails, 0 URLs, 0 lane ids | regex scan of the file |

On those numbers alone a history rewrite would genuinely close it, because there is no other copy
in the world. That was the case for option two, and it is wrong, for a reason nobody had checked.

### The names are not in that file. They are in the repository.

Counted at `HEAD`, **excluding** `nightrun.html`, word-boundary matched:

| | occurrences | tracked files |
|---|---|---|
| project A | 26 | 11 |
| project B | 18 | 11 |
| project C | 14 | 8 |
| project D | 3 | 2 |
| the vendored dependency | 51 | 22 |

They are in source (`routemap.py`, `soloroute.py`, `history.py`, `fleet.py`, `mcp_server.py`), in
two test files that use real project names as fixtures, in brand briefs, in memos, in the PRD, in
`hack.md`, and in `profile.html`. One of them is not a leak at all: the vendored dependency is
disclosed in the README on purpose, because the rules require disclosing pre-existing code.

**So rewriting history to remove one file closes nothing.** The map is distributed. Option two
costs a rewrite of every commit in the repository, since the file entered in the root commit, and
leaves the exposure standing.

### The recommendation

**Take option one, and do not call it closed.**

Done in this commit: `nightrun.html` is untracked and gitignored, with the reason written next to
the entry. It was never referenced by anything except as the default `--out` filename, so nothing
breaks. `nightrun-public.html`, the redacted render with zero occurrences, stays as the publishable
artifact.

That removes the one file where the names form a readable picture of the whole board, 164
occurrences in one render, and it is honest about what it does not do: the file stays in the log,
reachable by anyone who clones and runs `git log`.

**What actually closes B4 is a repository-wide pass over roughly 30 files**, deciding per name
whether it is a leak or a disclosure, and replacing the leaks with the `repo N` labels the redactor
already produces. That is a sized job, it is not this addendum, and it should not be confused with
the untracking above.

### And two that are mine

The first version of this audit documented the leak by reproducing it: the table in B4 listed all
the project names and their counts, so the audit file itself became one more place they appear. Now
corrected to counts without names. Writing down a leak is not a licence to copy it.

And the count was wrong. It was relayed to me as 164 occurrences of six project names, I verified
the arithmetic and not the semantics, and published it. One of the six is the ordinary English word
"cleared", which appears 50 times in that file as "the bar is actually cleared". The real figure is
**115 occurrences of five names**, and one of those five is this repository's own former codename.
Checking that a number adds up is not the same as checking that it counts what it says it counts,
which is the thing this whole project is about.

## Addendum 4: the name pass is done, and here is the number

**At `HEAD`, a stranger who clones this repository and reads the files sees zero occurrences of any
of Oscar's other projects.** Measured over every tracked text file, twelve names, word-boundary
matched: 51 replacements across 21 files, then 7 more where a redaction label had landed in
user-facing copy and needed a plausible example instead.

**In the history, 334 occurrences of those twelve names are still reachable** by anyone who clones
and runs `git log --all -p`. That count includes the removal commit itself, because deleting text
in git makes it appear one more time in the log. That is the residue option one always had, and it
is now measured rather than described.

So the two numbers a friend cares about are **0 at HEAD** and **334 in the log**, and only a
history rewrite moves the second, which as Addendum 3 established would rewrite every commit in the
repository.

What was deliberately left alone, and why, because a redaction that strips a required disclosure is
the same error facing the other way:

- **The vendored dependency and the two public sibling repositories.** Disclosed in the README on
  purpose. The rules require disclosing pre-existing code.
- **This repository's own former codename.** It is documented as its own former name in its own
  brand book. It maps nothing else.
- **`recon`.** Not a name. It is the sentinel the code uses for "landed in no repository", and
  `fleet.py` says so.

One more thing this pass caught, and it is a correction to the finding rather than to the fix. The
leak was reported as six names; one of the six is the ordinary English word "cleared". See the
correction under Addendum 3.

## The order to fix in

1. Merge and push the lane branch. B1 and B2 close together, and nothing else can be evaluated
   honestly until a friend and the author are looking at the same code.
2. Rule R5. The walkthrough cannot go out quoting a figure nobody chose.
3. Rule R3, or send the link as "read my runs" and say so.
4. C1 through C4, about an hour together.
5. R1 and R2, which are now funnel, not polish.
6. Re-run this audit on the merged result. A stranger check on a tree that has since changed is a
   claim about a thing that no longer exists.
