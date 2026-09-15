# Five-minute stranger trial · capture → preview → deliberate post → recovery → exact reply

For one person who has never seen the app. Local disposable data only. Nothing here reaches a hosted service or another person. Expected outcomes are what the committed shell showed on a 390 px phone viewport in `scripts/check-post-recovery.py`; screenshots in `docs/round2/screens/completion/`.

## Setup (one minute, done by the host, not the stranger)

```sh
git clone https://github.com/Morkeeth/agentgrinder-public.git && cd agentgrinder-public
python3 scripts/dev.py setup && npm install
python3 scripts/check-post-recovery.py     # boots the disposable backend and proves the path; prints the artifacts folder
python3 scripts/dev.py serve               # local site on http://127.0.0.1:8000, no database
```

The local site has no database, so steps 3 to 5 are shown from the walk's screenshots unless the host points the shell at a disposable backend the way the walk does. Steps 1, 2 and 6 run live on localhost.

## Script

| Min | Ask the stranger to | Expected visible outcome | Fail if |
|---|---|---|---|
| 0:00 | Open `http://127.0.0.1:8000/?post` and read the top panel. | They can say in one sentence what leaves their machine: counts and timing, never prompt text, code or file paths. | They believe their code or prompts are uploaded. |
| 0:45 | Run `python3 -m agentgrinder grind --harness cursor --push --push-url http://127.0.0.1:8000` (or open `docs/round2/screens/completion/01-offline-save-recovery-mobile.png`). | A preview headed **Preview your run**, a grey line starting "This export carries only: the project folder name, counts, timing…", an **Inspect all imported fields** disclosure, and a card labelled **not posted**. | They cannot find what is shared, or think the card is already public. |
| 1:30 | Write a title and caption, choose **Public feed and profile**, then (host) cut the network and press **Save run**. | Screenshot 01: a card under the button reading **Not saved. The service could not be reached.** with **Try again** and **Your runs**. Their caption and audience are still in the fields. The page did not navigate. | The caption is gone, the page moved, or nothing at all appears. |
| 2:15 | Restore the network, press **Try again** once. | Screenshot 02: the run opens at `/?run=…` with their caption; status says **Run published**. Exactly one run exists under **My runs**. | Two runs, or the run does not open. |
| 2:45 | Open the same capture link again, write a different caption, press **Save run**. | Screenshot 03: status reads **This capture was already saved as a run (Public). Opening it. The caption you typed here was not applied…** and the original run opens. Still one run. | A second run is created. |
| 3:30 | Paste a capture link with the last 40 characters cut off. | Screenshot 06: **This import link is incomplete**, "Nothing was posted", and a link to how to capture. | The landing page shows with no message. |
| 4:00 | (Host seeds 330 replies on the run as a second person, then hands the stranger the friend's "Open exact reply" link from Responses.) | Screenshot 07: the exact reply is on screen inside a blue-edged block that says it is shown on its own because it sits further back; focus is on that reply; **Back to Responses** is offered. | The page says the reply was removed, or the stranger has to scroll to find it. |
| 4:40 | Open a reply link whose id does not exist. | Screenshot 08: **That reply was removed or is not visible to you. The run is still here.** | An error, or a blank thread. |

## What this trial does not show

Hosted sign-in, real provider linking, and a second consenting person are not part of this trial. The manual "Post a run without a Cursor export" form has no duplicate guard; it is outside this journey and named in NIGHT-RETURN.md.
