# STRANGER-RECRUIT · Agent Grinder

**The gate:** one person who is not the author runs the cold path on their own machine and
publishes a coached run. Not a screen share, not a screenshot Oscar took. That single event moves
the Impact criterion off its weakest sentence, which today is that the hosted database holds 2
profiles and 2 runs and both are the author's.

**What to ask for:** two commands and one honest sentence back. Nothing else. Do not ask for a
star, a retweet, or feedback on the idea.

All URLs below were fetched on 3 September 2026 and returned HTTP 200.

---

## The three

### 1. Pete Hodgson · `moredip`

- https://github.com/moredip/session-share
- https://github.com/moredip · https://thepete.net · X `@ph1`

He built `session-share`, a Claude Code plugin that publishes the current session transcript to a
secret GitHub Gist and renders it at a URL. That is the same primitive with the verification left
out, which makes the pitch one sentence long. He is an independent consultant who writes publicly
about engineering practice, so he is likelier than the others to write something rather than only
run it. The repository has 2 stars, which means he is early enough that a message is interesting
rather than noise. Highest expected reply rate of the three.

### 2. Philipp Spiess · `philipp-spiess`

- https://github.com/philipp-spiess/claude-code-viewer
- https://github.com/philipp-spiess · https://spiess.dev · X `@PhilippSpiess`

`claude-code-viewer` is `npx claude-code-uploader`, which turns a transcript into a hosted page.
His pinned project is AgentLogs, described as a collaboration platform for agentic engineering.
He is the most on-target person found: session becomes a shared artifact is already his product
thesis, and the missing axis in every version of it is whether anything in the session was true.
Formerly on Tailwind CSS and React DOM, now at OpenAI, so the reply rate is lower and the reach
if he does reply is much higher.

### 3. Yoav Farhi · `yoavf`

- https://github.com/yoavf/ai-sessions
- https://github.com/yoavf · https://yoav.blog · X `@yoavf`

He runs `ai-sessions`, a hosted service for sharing Claude Code and Codex transcripts, plus an MCP
server that searches your own past sessions. He is the closest thing to a direct peer: he has
already decided that a session is a thing worth publishing, and he handles the multi-thousand
message case. He will understand the verified-per-turn number without any setup.

### Two reserves, if the three go quiet

- **Augusto Bastos · `augbastos`**, https://github.com/augbastos/devcard, an embeddable SVG card
  driven by Claude Code hooks and git hooks. Nearly no followers and a public email on his profile,
  so the easiest of anyone to reach, and the least distribution if he says yes.
- **Simon Willison · `simonw`**, https://github.com/simonw/claude-code-transcripts, 1.7k stars,
  publishes his own sessions with the dollar cost attached. The most reach of anyone in this
  space and the most heavily messaged. Use the repository issue tracker rather than a DM, and only
  once there is a video to point at.

Not on this list on purpose: `stravibe.vercel.app` is live and is the nearest competitor, but the
site names no person and no handle, and a search found no maintainer. Do not guess one.

---

## The message

Paste as is. Replace only the first line per person. Plain, numeric, no emoji, no exclamation
marks, and no adjective doing work a number could do.

For Pete Hodgson:

```text
Hi Pete. I found session-share while looking at who else is turning a coding session into
something you can send to a person.

I built a thing next to it: it takes one Claude Code or Cursor session and produces a card, and
before the card prints a number a small agent checks the session. It reads the transcript through
five tools, checks every claim the agent made against the tool result in that claim's own turn,
checks whether every file the run said it wrote exists on disk, and asks git which of them
landed. The verdict tool refuses any number the other four did not return.

Two commands, no key, no account, nothing leaves your machine:

  git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
  pip install -e ".[coach]"
  python3 -m agentgrinder grind --coach

The one thing I want back: does the verdict match what you remember actually happening in that
session, or is it flattering you. The claim rule is v0 and I think it over-counts, and I would
rather hear that from someone else's transcript than keep testing it on my own.

Oscar
```

For Philipp Spiess, swap the first paragraph:

```text
Hi Philipp. I found claude-code-viewer, and then AgentLogs, while looking at who treats a session
as an artifact rather than a log file.
```

For Yoav Farhi, swap the first paragraph:

```text
Hi Yoav. I found ai-sessions while looking at who else publishes coding sessions to a URL.
```

If a reply comes back positive, the second ask, and only then:

```text
If the card was worth keeping, grind --push publishes it to a page. That would make you the first
person who is not me with a run on there, which is a number I would rather stop having to write
as 1.
```

---

## Rules for sending

- Oscar sends these. An agent drafts, a human sends. Nothing here is auto-sent.
- One channel per person, whichever their profile actually lists. A GitHub issue on their own
  repository is not the right door for this; it is a message about a different project.
- No emoji, no exclamation marks, no "quick question", no "would love your thoughts".
- Send before the video exists. A reply that arrives on 12 September is still in time to change
  the Impact sentence in the description; one that arrives on 15 September is not.

## Results

| Who | Sent | Replied | Ran it | Published | What they said |
|---|---|---|---|---|---|
| Pete Hodgson | | | | | |
| Philipp Spiess | | | | | |
| Yoav Farhi | | | | | |

Update the Impact paragraph in `docs/DEVPOST-DESCRIPTION.md` the moment a row here says published.
The sentence to replace is the one beginning "Two profiles today."
