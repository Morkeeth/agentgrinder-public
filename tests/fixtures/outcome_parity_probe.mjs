// Reads a JSON list of runs on stdin and prints, for each, whether the browser contract accepts it.
// tests/test_outcome_upload.py compares that against the Python export so the two rule sets cannot drift.
import { createRequire } from 'node:module';
const contract = createRequire(import.meta.url)('../../site/run-contract.js');
let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const verdicts = JSON.parse(raw).map((run) => {
  try { contract.validate(run); return true; } catch (_) { return false; }
});
process.stdout.write(JSON.stringify(verdicts));
