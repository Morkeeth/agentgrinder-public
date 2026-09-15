# The site: constraint list and one device

*4 September 2026. No pixels, no comps, no palettes. Written because three directions that differ
only in colour are one direction, and the way to avoid producing three of those is to write down
what the page is for first.*

---

## First, the premise, checked

I was told the site is "arranged to make somebody read". Read at the object, that is not quite it,
and the real shape is worse because it is harder to see.

The landing block, in order: name, tagline, a one-line description, a panel headed **2-minute
demo** carrying **four commands**, a features row listing **six things** (vibe stamps, roast shape,
ACK bingo, rig heist, ghost grinds, claim-your-handle cards), **three buttons**, then the example
card.

The command is not buried. It is at position five. **The problem is that there are four of them,
plus six features, plus three buttons, before the visitor reaches anything of their own.** The page
does not ask somebody to read. It asks somebody to *choose*, thirteen ways, and offers no default.

And the first of the four commands is `pip install -e . && agentgrinder flex`, which this project's
own README documents as **failing** on the Python macOS ships, because that pip predates PEP 660.
So the page's opening instruction is one the repository already knows does not work for a stranger.
That is not a design finding, it is a correctness finding, and it should be fixed whatever happens
to the layout.

---

## The constraint list

### Who lands here, and from where

1. **A friend Oscar sent a link to.** Technical, curious, no context, ten seconds of patience. The
   dominant case now, and the one the current page was not built for.
2. **A hackathon judge**, on the clock, who will not debug anything.
3. **A stranger from a post**, colder than either.

All three arrive **without an account and without having run anything.** None of them has data on
this page. That is the single fact the current layout ignores: it is laid out as though the visitor
already has runs to look at.

### What they must understand in ten seconds

- Your coding agent says it shipped. **This checks.**
- It reads transcripts **you already have**, locally, and uploads nothing.
- Every number on it either names its source or shows a dash that names what is missing.

Not: what a vibe stamp is. Not: what ACK bingo is.

### The one action

**Run one command on their own machine.**

Not sign in. Not read the methodology. Not browse the feed. Signing in cannot even be the second
action, because the anonymous door does not exist yet: publishing needs a GitHub account, which
half these visitors will not do on a stranger's link.

### What must be on the page

- The one command, exactly once, copyable, and it must be a command that **works on a stock Mac**.
- One real card with real numbers, visible logged out. This already exists and is the strongest
  thing on the page.
- The measured limits, because for this audience the limits are what earn the trust: the headline
  that sits **below** the harness it scores, the harness with an **empty cell**, and the 78.6% of
  verified resting on the weaker of two rules.
- A link to the methodology for the reader who wants it. A link, not the content.

### What is forbidden

- **More than one command.** Four commands is a menu, and a menu is what you offer somebody who
  already knows what they want.
- **The features row.** Six named features before the visitor has seen anything of their own.
- **A dashboard shape**: KPI tiles, a wall of stat cards, a hairline-ruled metric grid. The card
  itself is a dense instrument and that is correct; the page around it must not repeat that rhythm
  or the whole thing reads as one dashboard.
- **Any number without its source next to it.** The product's entire argument. A page that breaks
  it is the argument losing on its own home page.
- The hackathon deadline badge, for the friend audience. See the open question below.

---

## The one device

**The page is your card, and it is empty, and every empty cell says which fact it is missing and
what supplies it.**

Not a hero. Not an explainer. The visitor lands on a run card with their name slot blank and every
number showing a dash, and each dash carries the sentence the product already writes for it:

```
verified per turn   [dash]   needs verified claims, artifacts produced
files touched       [dash]   needs a transcript on this machine
reach               [dash]   needs a repository and a session window
correction rate     [dash]   not measured yet: no harness records this
```

*(`[dash]` stands for the character the card actually prints, which this document is not permitted
to contain.)*

One command sits under it. Run it and your own card renders in place of the empty one.

### Why this device and not another

It is taken from the subject rather than from a component library. **The dash that names what it is
missing is already the product's core rule**, enforced in `metrics.py` and in every tooltip: no
number is ever defaulted to zero, and a dash is never blank. The device is not invented for the
page; it is the thing the product already does, made the size of the page.

**It makes the argument the prose cannot.** "We never invent numbers" is a claim a visitor has to
take on trust. A card of dashes, each naming its missing fact, *is* that claim, performed, before
they have given anything. And it makes the one action structurally inevitable: the page is visibly
incomplete, and exactly one thing completes it.

**It is not a dashboard.** A dashboard shows data. This shows absence, with reasons. Same
components, opposite argument, which is the only way to use a dense instrument without reading as
one more metrics wall.

### The removal test

Delete it and what is lost?

- The visitor no longer knows what the tool measures, because the empty cells are the field list.
- They no longer know that a missing number is *named* rather than hidden, which is the whole
  differentiator against every dashboard that shows a confident 0.
- They no longer have a reason to run the command, because nothing on the page is incomplete
  without them.

Three things lost, none of them decoration. It passes.

### The runner-up, and why not

**The empty Cursor cell in the per-harness table.** A precision cell left blank on purpose, with
the counts printed beside it, because four predicted positives cannot support a number. It is a
genuinely strong device and it is the same family as the one above, which is the reason not to use
it: it is one cell in one table, and it argues about the calibration rather than about the tool.
It belongs on `/methodology`, where it already is. **The empty card generalises it to the page.**

The other candidate, the check that cannot go red, is the best *sentence* this project owns and it
belongs in the reel rather than on the landing page. It is a story about the makers. The visitor
does not care about the makers yet.

---

## What I am NOT doing, and why

**No comps, no palette, no typeface.** Gate 1 says directions must be different languages, not
variations, and the way to guarantee variations is to start drawing. This document is Gate 0. If
the constraint list or the device is wrong, everything built on it is wasted, and four directions
have already been rejected today.

**I have not touched C4 or C5.** The empty `rig` card that invites a stranger to share "0 MCPs, 0
skills", and the Sep 14 nav badge. Both are real. But fixing them one at a time, right now, is
exactly the whack-a-mole the guide names: C4 is a *symptom of this device being absent*, because an
empty rig card that says nothing is the same defect as an empty page that says nothing, and the
device fixes both or neither. Bank them and fix them cohesively.

C5 stays a genuine question rather than a papercut, and it is not mine: **the deadline badge is
right for the judge audience and wrong for the friend audience, and the site currently serves
both.** That is a constraint conflict, and per step 3, a conflicting constraint goes back to the
list rather than getting patched. Oscar picks the audience; the badge follows.

---

## The one thing to decide before anything is drawn

**Is the landing page for the friend, or for the judge?** Every constraint above is written for the
friend, because that is who Oscar said he is sending it to. If it is still primarily the Devpost
demo until 14 September, several of these constraints change and the device may not survive them.
