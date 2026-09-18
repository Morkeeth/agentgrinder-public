"""Large private imports shrink without changing the run contract."""
import base64
import gzip
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import unquote

import pytest

from agentgrinder.push import export_run, import_url


ROOT = Path(__file__).resolve().parents[1]


def long_run():
    return {
        "harness": "Cursor",
        "turns_typed": 80,
        "tool_calls": 5000,
        "rhythm": [3, 0, 2, 1] * 6,
        "route": [index % 8 for index in range(5000)],
        "ridge": [index % 6 for index in range(50)],
        "ridge_basis": "wall-time",
        "ridge_wall_seconds": 7200,
        "worker_bins": [0] * 20 + [2] * 20 + [0] * 10,
        "commit_bins": [12, 31, 44],
    }


def token(url):
    return url.split("#import=", 1)[1]


def test_small_imports_keep_the_legacy_browser_compatible_encoding():
    run = {"harness": "Cursor", "turns_typed": 2}
    encoded = token(import_url(run, "https://strive.example"))
    assert not encoded.startswith("gz.")
    assert json.loads(base64.b64decode(unquote(encoded))) == export_run(run)


def test_large_imports_are_gzipped_and_decode_to_the_validated_export():
    run = long_run()
    encoded = token(import_url(run, "https://strive.example"))
    assert encoded.startswith("gz.")
    compressed = encoded.removeprefix("gz.")
    compressed += "=" * (-len(compressed) % 4)
    decoded = json.loads(gzip.decompress(base64.urlsafe_b64decode(compressed)))
    assert decoded == export_run(run)


def test_large_import_url_is_materially_shorter_than_the_legacy_url():
    payload = json.dumps(export_run(long_run()), separators=(",", ":")).encode()
    legacy = base64.b64encode(payload).decode()
    compressed = token(import_url(long_run(), "https://strive.example"))
    assert len(compressed) < len(legacy) // 4


@pytest.mark.skipif(not shutil.which("node"), reason="node is not on this machine")
def test_browser_decompresses_then_runs_the_existing_validator():
    html = (ROOT / "site/index.html").read_text()
    decoder = html[
        html.index("async function decodeImportPayload("):
        html.index("\nasync function importRun()")
    ]
    encoded = token(import_url(long_run(), "https://strive.example"))
    script = decoder + """
const contract=require(process.argv[1]);
decodeImportPayload(process.argv[2])
  .then(run=>console.log(JSON.stringify(contract.validate(run))))
  .catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "site/run-contract.js"), encoded],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == export_run(long_run())
