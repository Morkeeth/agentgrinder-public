# Bedrock coach take: command and receipt template

Status: TEMPLATE, not a receipt. Nothing below has been run. The keyless path has; this is the
one run the coach has not had, because it needs Oscar's AWS credentials and it spends money.
Fill every `<...>` from the terminal, paste the output verbatim, and delete this paragraph. A
receipt with a number typed from memory is not a receipt.

## Before the run

- The AWS account has Bedrock model access enabled in the region below for the model below.
- Credentials are in the environment for THIS shell only, never in a file inside the repo:
  `aws sts get-caller-identity` returns the expected account. Paste the account id, nothing else.
- Read `agentgrinder/coach/agent.py` BEDROCK_BANNER once: the run sends the claim lines and
  tool-result snippets of the chosen sitting to Amazon Bedrock. Pick a sitting whose claim lines
  you are willing to send. The bundled fixture is the safe first choice.

## The command

```bash
cd <clone of Morkeeth/agentgrinder at main>
pip install -e ".[coach]"
export AWS_REGION=<region, e.g. us-east-1>
# the Strands default is Amazon Bedrock with its default model id; to pin one:
# export STRANDS_MODEL_ID=<model id>   (check the Strands BedrockModel docs for the current variable)
python3 -m agentgrinder coach samples/sample_session.jsonl --model bedrock 2>&1 | tee docs/receipts/bedrock-coach-<date>.txt
```

Expected on screen, in this order: the BEDROCK banner (before any network call), then
`GRIND COACH  [MODE: strands agent loop · Amazon Bedrock ...]`, then `tools dispatched N (by the
Strands event loop; hook logged N)`, then the verdict. If the run prints `DEGRADED`, the model
never ran: paste the banner's exception line into the receipt and stop.

Then the same on a real sitting of your own, if the fixture run was clean:

```bash
python3 -m agentgrinder grind --coach bedrock --no-open
```

## What the receipt must record

| Field | Value | Source |
|---|---|---|
| Date and time (CEST) | `<...>` | the shell |
| Commit under test | `<git rev-parse --short HEAD>` | git |
| Region and model id | `<...>` | the environment, the run's first lines |
| Sitting | fixture / own sitting `<project, start time>` | the report's `sitting` line |
| Tools dispatched (SDK) | `<N>` | the report's `tools dispatched` line |
| Hook logged | `<N>` | same line |
| Order of tool calls | `<read_run, check_claim x?, ...>` | the report |
| write_verdict accepted first time | yes / no; if no, the refusal reasons | the `--json` run, `coach_numbers` present or not |
| Verdict numbers | typed `<n>`, claims `<v> of <c>`, artifacts `<a> of <w>`, commits `<n>` | the report |
| card agrees | yes / NO | the report |
| Paragraph the model wrote | paste verbatim | the report |
| Plan the model wrote | paste verbatim | the report |
| Cost | `<USD from the AWS console, after the fact>` | AWS billing, not an estimate |
| Anything the model did that the policy would not | e.g. skipped a claim, called write_verdict twice | compare with a `--model local` run on the same sitting |

## The comparison that makes it worth doing

Run `--model local` on the same sitting and put the two `tools dispatched` lines and the two
verdict blocks side by side. The numbers must be identical (they come from the same tools on the
same sitting). Only the paragraph and the plan may differ. If a number differs, `write_verdict`
should have refused it; if it did not, that is a defect in `agentgrinder/coach/tools.py` and the
receipt says so.

## Where it lands

- The pasted output: `docs/receipts/bedrock-coach-<date>.txt` (create the directory).
- This file, filled in, renamed to `docs/BEDROCK-COACH-RECEIPT-<date>.md`.
- One line in `README.md` under "The grind coach", after the three modes: the date, the region,
  the dispatched count and the cost, with a link to the receipt.
