/**
 * ONE TABLE OF PROJECT NAMES, THROUGH ALL THREE READERS.
 *
 * A capture names a project after the workspace directory, and the workspace directory is a
 * flattened absolute path, so the account name travels with it. The rule that removes it lives
 * in three places — the Python reader, the browser contract and the server card — and a rule in
 * three places drifts. This runs the same cases through the two JavaScript ones and prints the
 * results; tests/test_project_label_parity.py runs the same cases through Python and compares.
 */
import { createRequire } from "node:module";
import { projectNameForTest } from "../../server/public-run.mjs";

const require = createRequire(import.meta.url);
const contract = require("../../site/run-contract.js");

const cases = [
  "Users-morkeeth",
  "-Users-morkeeth",
  "Users-alice-code-myapp",
  "-Users-bob-work-thing",
  "home-carol-src-thing",
  "-home-dave-proj",
  "agentgrinder-public",
  "the-fair",
  "session",
];

const out = {};
for (const value of cases) {
  out[value] = {
    contract: contract.projectLabel(value),
    server: projectNameForTest({ project: value }),
  };
}
process.stdout.write(JSON.stringify(out));
