# Tonight live review · 15 September 2026

## Evidence boundary

Reviewed `https://agentic-strava.vercel.app` signed out and read-only at 390 × 844 and 1280 ×
900. No hosted sign-in, Save, follow, ACK, reply, SQL, Auth change or deployment was attempted.
`/api/health` returned:

```json
{"service":"pacecard","database":"ready"}
```

The live index was 136,849 bytes with SHA-256
`a238ddbedf2a6e1e45e4b8c8b3785ff50d43fd0682b11da33b615a03fb3796ea`. It
matched the reviewed `main` source except for the expected browser database URL and publishable
key substitution. That is a source observation, not a deployment receipt. The latest supplied
Vercel receipt remains `726f8a57`.

The signed-in walk used labelled TEST DATA against the disposable local PGlite service. It made
no production request or claim about real people.

## Signed-out live review

| Path | Phone and desktop observation | Friction / action |
| --- | --- | --- |
| `/` | The white SAMPLE card and blue activity trace are the first visual on phone and remain the strongest element on desktop. SAMPLE and repository example provenance are explicit. No output is attached, so it does not imply shipped work. | Keep. The intro named Cursor, Claude Code and Codex but omitted priority harness Grok Bot; this PR adds it. |
| `/?explore` | Feed is honestly empty: “No public runs yet,” followed by what a real card will contain and a Post link. No profiles, output or engagement are fabricated. | Keep the empty state. A live real card was unavailable, so caption/output hierarchy was verified with disposable data instead. |
| `/?post` | The capture → preview → choose audience promise is clear and neither viewport overflows. The live page is Cursor-only at first glance and gives an optional coach more space than the core action. | This PR removes the coach block from the signed-out Post path, names Cursor and Grok Bot, and keeps one link to Grok export preview steps. |
| Sign-in dialog | “Keep your run,” GitHub, email-link privacy and private-until-Public copy are clear. Opening the dialog causes no write. | The desktop header said “Sign in with GitHub” although email is also offered. This PR shortens the header action to “Sign in”; provider choice remains in the dialog. Production callback allowlisting is still unverified. |
| `/?inbox` | Signed out, Responses explains ACKs/replies/followers and asks for sign-in. It does not pretend the inbox is empty. | Keep. The actual signed-in empty state was checked only against disposable local data. |

Screenshots attached to the review PR cover Feed, SAMPLE, Post, sign-in and signed-out Responses at
both viewports. There was no horizontal overflow and no page error in the ten-page live pass.

## Disposable signed-in review

The existing round-2 browser walk passed 40 checks at 390 × 844 and the same 40 checks at 1280 ×
900. It covered:

- imported Cursor capture → private preview → explicit Public choice → Save;
- caption-first card preview, harness/project/time context and unknown unsupported metrics;
- follow → ACK → reply → unread Responses → exact reply → back to Responses;
- a zero-notification state without a false blue badge and the signed-in empty Responses actions;
- cancelled sign-in draft recovery, duplicate handle refusal, deleted/private targets and block
  enforcement; and
- no horizontal overflow or JavaScript page errors.

The disposable run proves browser behavior with fixtures, not hosted OAuth, production data,
two-person use or later-day return.

## Bounded polish in this PR

- Caption and output link now precede run metadata; builder, project, harness and time remain clear.
- Cursor and Grok Bot are named on Post, and harness text is visually stronger without adding a
  badge or new brand system.
- The white card, blue trace, hairlines, calm type and unknown measurements are unchanged.
- Cursor and Grok Bot docs use `https://agentic-strava.vercel.app` for a deliberately selected
  hosted preview; neither command saves automatically.

## Tonight handoff

Merge **#27 → #28 → #23**, then deploy the merged tip with a new receipt. Confirm the Auth
allowlist for `https://agentic-strava.vercel.app`, then run the two-consenting-person walk. #26 and
#29 follow the core; do not expand merged #20.

Exact Codex paste:

```text
merge #27+#28+#23, deploy tip, confirm Auth allowlist, then two-person walk.
```
