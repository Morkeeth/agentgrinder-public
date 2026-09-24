# Continue a public run in a coding harness

Research checked on 15 September 2026. Product behavior was tested locally on
15 September 2026.

## Decision

A STRIVE run card cannot honestly promise "Fork this run." The public card
does not contain a private transcript, and the three harnesses do not accept one
portable public session format.

The honest action available today is "Continue in Cursor" for a run captured
from Cursor. It opens a new Cursor chat with a reviewable prompt made only from
the card's public project, recorded intent, caption, and HTTP or HTTPS output
link. It does not restore the original conversation or automatically run the
prompt.

Every saved card with public context also offers "Copy prompt." This is the
fallback when STRIVE has no supported deep link, the desktop app is absent, or
the browser refuses to open a custom URL scheme. The card labels the harness
that captured the run.

## What each harness accepts

| Harness surface | Accepted input | What opens | Can STRIVE call this a fork? |
| --- | --- | --- | --- |
| Cursor prompt deeplink | A URL encoded prompt string in the `text` parameter | A new chat with the prompt prefilled for review | No. No transcript or repository parameter is documented for this link. |
| Cursor shared transcript | A Cursor hosted `cursor.com/s/<id>` transcript created by the chat owner | A read-only full conversation; "Fork to Cursor" continues with that shared history | Only for an actual Cursor shared transcript. STRIVE does not create or store one. |
| Claude Code `--resume` | A Claude session ID or name, or the absolute path to a Claude Code `.jsonl` transcript | That native Claude Code session | No. A STRIVE prompt and a rendered `/export` text file are not a native resumable session. |
| Codex app deeplink | A prompt, an absolute local workspace path, a Git remote URL, or a local thread ID | A new local chat or an existing local chat | No. The documented link is local app routing, not a public transcript share. |
| STRIVE fallback | The same generated public prompt copied to the clipboard | A prompt the reader can paste into any harness after opening the right repository | No. It is explicitly a new start from public context. |

## Cursor evidence

[Cursor Deeplinks](https://cursor.com/docs/reference/deeplinks) documents:

* `cursor://anysphere.cursor-deeplink/prompt?text=...`
* `https://cursor.com/link/prompt?text=...` as the web form
* `text` as the only parameter in the prompt examples
* a prefilled chat that the user must review and confirm
* no automatic execution
* an 8,000 character maximum after URL encoding

The same page also documents command links with `name` and `text`, and rule
links with `name` and `text`. Those create reusable Cursor configuration and
are not session continuation.

[Cursor Shared transcripts](https://cursor.com/help/ai-features/shared-transcripts)
documents public links in the form `cursor.com/s/abc123` and the recipient's
"Fork to Cursor" action. This is the only documented true transcript fork in
this research. It shares the full conversation, including code snippets, tool
calls, and results. Cursor applies best-effort secret redaction and warns that
redaction is not guaranteed. The feature is limited to Teams and Enterprise,
with public links available on Teams and team links on Enterprise by default.
It is unavailable with No Storage Privacy Mode.

STRIVE must not manufacture a shared transcript from a private local capture.
Doing that would change the privacy boundary and would still depend on a paid
Cursor sharing feature.

## Claude Code evidence

[Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
documents `--continue`, `--resume`, and `--fork-session`. Current documentation
allows `--resume` to receive a session ID, a name, or the absolute path to a
session's `.jsonl` transcript file.

[Claude Code Manage sessions](https://code.claude.com/docs/en/sessions)
documents continuous local transcript storage and `/export`. It says the JSONL
entry format is internal and can change between versions. `/export` produces a
rendered transcript for a person to read. The docs do not say that an arbitrary
text file, a foreign harness transcript, or a STRIVE run card can be imported
as a resumable Claude Code session.

This means a native Claude transcript file can resume on a machine that has the
file, but a public STRIVE card cannot safely create that file from card fields.
Copying the bounded public prompt into a new Claude Code session is the honest
fallback.

## Codex evidence

[Codex app commands and deep links](https://developers.openai.com/codex/app/commands)
documents these chat links:

* `codex://threads/<thread-id>` opens an existing local chat by technical ID.
* `codex://threads/new` opens a new local chat.
* `codex://new?prompt=...` prefills a new composer.
* `path` selects an absolute local workspace directory.
* `originUrl` matches a current workspace root by Git remote URL.

The page says `prompt`, `path`, and `originUrl` can be combined and values must
be encoded. The prompt is not sent automatically. It does not document a public
transcript share URL that another user can fork.

[Codex CLI reference](https://developers.openai.com/codex/cli/reference)
documents `codex resume` and `codex fork` for saved local interactive sessions.
Those commands require local Codex session state. They do not turn a public run
card into a portable transcript.

Codex could be a later direct target because its app link accepts both a prompt
and `originUrl`. STRIVE should add it only after an installed-app test confirms
the exact behavior and the public output link can be identified as the intended
Git remote without guessing.

## Implemented prompt boundary

The generated prompt is capped at 1,500 characters before URL encoding. Its
allowlist is:

1. project name
2. recorded intent, represented by the public run title
3. caption
4. an HTTP or HTTPS output link

The builder does not read transcript, message, tool-result, code, path, private
note, measurement, profile, or engagement fields. Card text is quoted and
called untrusted context so a caption cannot silently become an instruction.
The URL is produced with `URL.searchParams`, not string concatenation. If URL
encoding takes the link beyond Cursor's documented 8,000 character limit, the
direct action is hidden and "Copy prompt" remains.

## macOS manual verification

The development environment is Linux and does not have the macOS Cursor app, so
the custom URL launch remains unverified.

1. On macOS, install or update Cursor and open any local repository.
2. Start STRIVE with `python3 scripts/dev.py serve`.
3. Open a saved Cursor run card at `http://127.0.0.1:8000/?run=<id>`.
4. Confirm the card says "Captured from Cursor" and offers "Continue in Cursor"
   and "Copy prompt."
5. Press "Copy prompt" and save the clipboard text for comparison.
6. Click "Continue in Cursor" and approve the browser prompt to open Cursor.
7. Confirm Cursor opens a new chat in the app and prefills the exact copied
   prompt without sending it.
8. Confirm the text is at most 1,500 characters and contains only the public
   project, recorded intent, caption, and output link shown on the card.
9. Repeat in a browser that blocks the custom scheme. Confirm "Copy prompt"
   still supplies the same text.
10. Open a Claude Code or Codex card. Confirm there is no Cursor continuation
    button and "Copy prompt" remains available.
