# Add a `--json` flag

Add an optional `--json` flag to `summary.py`.

## Required behavior

- Without the flag, preserve the current human-readable output exactly.
- With `--json`, print one JSON object with the keys `file`, `lines`, `words` and `characters`.
- `file` is the input file name, not its absolute path.
- Use only the Python standard library.
- Add focused tests for the existing output and the JSON output.

Run the finished CLI from this directory:

```sh
python3 summary.py --json README.md
```

Post the resulting agent run to Agentic Strava and choose segment 01 only after you have run the tests.
