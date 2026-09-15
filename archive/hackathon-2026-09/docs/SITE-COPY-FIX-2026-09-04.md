# Two sentences on the landing page that the default command does not do

*Draft only. `site/index.html` is NOT edited. Site copy is Oscar's, and this is the replacement
text plus the reason, ready to paste.*

## What the page says now

`site/index.html:1010`, the first line a logged-out visitor reads:

> Your agent says it shipped. A second agent checks before the card shows a number.

`site/index.html:1141`, the section heading for the featured run:

> your agent says it shipped, a second agent checks first

## Why it is not true of what a friend runs

The command the page and the README both hand a visitor is `python3 -m agentgrinder grind`. That
runs **no coach**. The referee is `grind --coach`, which additionally needs
`pip install -e ".[coach]"` and a Python 3.10 or newer interpreter, neither of which is in the
one-line install the page advertises.

So a friend follows the page exactly, gets a card, and no second agent checked anything. The
sentence is true of a command they were not told to run.

**The second agent is real when you do run it.** `--coach` builds a genuine `strands.Agent` with
five tools, a hook that logs every dispatch, and a `write_verdict` that refuses any number no tool
returned. What the default mode is *not* is a language model: `coach/agent.py:7` calls its token
generation a deterministic policy, and the report prints that under NOTE on every run. That
distinction is documented honestly everywhere except here, and "agent" is defensible for a real
Strands loop, so it is not the sentence that needs fixing. The command is.

## The replacement

**Line 1010:**

> Your agent says it shipped. Add `--coach` and a second agent checks every claim before the card
> shows a number.

**Line 1141:**

> your agent says it shipped, `--coach` puts a second agent on it

## Why this wording

It keeps the whole claim, which is a good one and is the product's argument. It moves the claim
from the default command, where it is false, to the flag where it is true, and it does that in four
extra words. A visitor who reads it now knows the referee is a thing they opt into, which is also
the honest description of something that needs an extra install.

## The alternative, if he would rather not qualify the headline

Make `--coach` the default and degrade loudly when the SDK is missing. That is a bigger change,
it makes the advertised one-liner slower and dependent on an install, and it is not a copy fix. It
is listed here only so the cheap option is a choice rather than the only thing anyone thought of.
