# VIDEO SHOTLIST · Agent Grinder · Agents for Humans

Target length **2:55**. The rules allow 5 minutes; a judge watching 7,262 entries does not. The
pitch must cover the problem, who it is for, and why it matters, and the rules accept screen
recording plus voiceover with nobody on camera.

**The signature moment is shot 5**: the coach refuses a number the session claimed, and then the
card prints the number the tools did back. Everything before it sets that up and everything after
it is the consequence. If a cut has to lose 20 seconds, it comes out of shots 2, 8 or 9, never 5.

---

## Before you record

| # | Step | Command or click | Why |
|---|---|---|---|
| P1 | Fresh clone into a clean directory, work only from it | `git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder` | the judge's path is the one on screen |
| P2 | Install the coach in a venv | `python3 -m venv .venv && ./.venv/bin/pip install -e ".[coach]"` | keeps the prompt short and the install real |
| P3 | Do one real 20 minute session inside the agentgrinder clone, then stop typing for 30 minutes | any coding-agent session in that directory | so shot 6's grind trace shows this project's own files, not another repo's paths |
| P4 | Terminal at 1280x720 or larger, font large enough to read on a phone, light background | | judges scrub on small screens |
| P5 | Cold review pass: watch shots 1 to 9 once with the sound off before recording anything | | you cannot see your own demo's bugs |
| P6 | Nothing to do. A coached run is already published and shot 8 points at it | open `https://agentgrinder.vercel.app/?run=28d5d0b7-eda2-4d94-a83c-580d2e3b75b2` once to confirm it loads | verified 3 September: 3.67 verified per turn, "verdict produced by 37 tool calls", the paragraph and the plan all render |

**Never on screen.** The name MAGNET, the repository `Morkeeth/agents-for-humans`, the word
"engine library", the README's disclosure paragraph, or any second product. The disclosure belongs
in the written Devpost description, where a judge reads it as provenance. On screen there is one
product. A second name in a demo costs the viewer the thread, and this entry has one thread.

Also never on screen: another client's repository name, a home directory path, an API key, the
Supabase service key. Use the clone and the bundled sample.

---

## The shots

| # | In | Out | On screen | Command or click | Say over it |
|---|---|---|---|---|---|
| 1 | 0:00 | 0:20 | Terminal, the authorship tally printing | `python3 -m agentgrinder authorship` | "Your coding agent says it fixed the test. You have no way to check. It is worse than that. This is one session log. Three hundred and thirty four records are marked as coming from the user. Twelve of them, three point six percent, were typed by a person." |
| 2 | 0:20 | 0:38 | The same output, cursor on the `human` row, then the sum line | hold, no new command | "The rest are tool results and injected context. Every session dashboard built on that field is inflating the number it shows you. And a twenty twenty five trial found developers believed an agent made them twenty percent faster when the stopwatch said nineteen percent slower." |
| 3 | 0:38 | 0:52 | `agentgrinder demo` runs, the card opens in the browser, scroll to the five numbers | `python3 -m agentgrinder demo` then open `card.html` | "Agent Grinder turns one coding session into a card. Five numbers. The headline is verified work per typed turn: what your prompts actually bought." |
| 4 | 0:52 | 1:22 | The coach report printing, the tool list visible | `python3 -m agentgrinder coach samples/sample_session.jsonl` | "Before the card prints a number, an agent referees the session. Five tools, built with Strands. It reads the run. It checks every claim against the evidence in that claim's own turn. It asks the disk whether every file the run promised exists. It asks git which of them landed. Eight tool calls, dispatched by the Strands event loop, counted by a hook on the after tool call event. The mode is printed every time: this one is keyless and offline." |
| 5 | 1:22 | 1:52 | **The refusal.** The script prints the offered verdict, then `accepted: False` and the two reasons | `python3 scripts/show-refusal.py` | "Here is the part that matters. The tools verified one claim of two, and one file of two. Now I hand the verdict tool a verdict that says two and two, the flattering version. It refuses. Claims verified: you wrote two, the tools returned one. Artifacts produced: you wrote two, the tools returned one. It cannot write a number a tool did not return. A card with no verdict is available. A card with a wrong verdict is not." |
| 6 | 1:52 | 2:18 | `grind --coach` runs, then the card in the browser, scrolled to the verdict block | `python3 -m agentgrinder grind --coach` then open `grind.html` | "So this is my real session, on this repository. The card takes the numbers the coach checked, and it says where they came from: verdict produced by four tool calls, Strands agent loop. Verified per turn, and every claim it counted has a tool result behind it in its own turn." |
| 7 | 2:18 | 2:32 | Scroll one line down to the series verdict, then the grind trace | hold on `grind.html` | "Next to it, this session against your last session on the same project. Helped, hurt, or baseline, because one reading is not a trend. And the trace: one row per file, your typed prompts as ticks, and the longest stretch nobody typed through." |
| 8 | 2:32 | 2:42 | Browser, the hosted card, scrolled so the headline and the coach line are both in frame | open `https://agentgrinder.vercel.app/?run=28d5d0b7-eda2-4d94-a83c-580d2e3b75b2` | "Sharing is a click you make. This one is published. Three point six seven verified per turn, three of seven claims with evidence, verdict produced by thirty seven tool calls. Nothing is uploaded until you say so." |
| 9 | 2:42 | 2:55 | Back to the terminal, `pytest -q` printing the green line (61 tests at commit 0fed2c7; read the count off the screen on the day, it moves) | `python3 -m pytest -q` | "This is for anyone whose day is now judgment over an agent's output: engineers, and the people who have to trust what an agent reports. It matters because the alternative is a number nobody checked. Agent Grinder. An agent checks your session before the card counts it." |

Total 2:55. Shot 2 is the first cut if it runs long; shots 8 and 9 can merge into one 12 second
close if the recording drifts past 3:10.

---

## The voiceover script

Local text to speech is already built and free (Kokoro 82M, runs on
CPU, no key, no signup, nothing leaves the machine). Do not pay for a TTS service for this.

Save the "Say over it" column as one line per line of the file, then:

```bash
cd <your local text-to-speech checkout>
./kvenv/bin/python vo.py scripts/agentgrinder-demo.txt \
  -o renders/agentgrinder-demo.mp3 --preset demo
```

Voice directives go at the top of the script file. `@voice bm_george` with `@lang b` is the
deep British read used before; `af_heart` or `bf_emma` if a lighter read fits the pace better.
`@speed 1.0` is natural; the previous trailer needed 1.30 to stop dragging, so listen once before
committing. Oscar's own voice is also fine and the rules do not care.

---

## Uploading

- YouTube or Vimeo, public, not unlisted. The rules say public.
- Title: `Agent Grinder: an agent checks your coding session before the card counts it`
- Description: the tagline, the repository link, the live link, and one line naming Strands Agents
  and the five tools.
- Under 5 minutes. This cut is under 3.

---

## The two failure modes this shot list is built to avoid

1. **Two products in five minutes.** Solved by the never-on-screen list above. One name, one
   thread, one card.
2. **A demo that shows a tool being run rather than a claim being tested.** Solved by shot 5. Most
   agent demos show the happy path. This one shows the agent refusing, which is the only thing a
   viewer cannot get from any other entry, and it is thirty seconds long on purpose.
