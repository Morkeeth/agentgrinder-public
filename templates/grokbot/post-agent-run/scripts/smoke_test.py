"""Run the installed STRIVE Grok kit against its bundled labelled sample."""
import base64
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlsplit

KIT = Path(__file__).resolve().parents[1]
PREVIEW = KIT / "scripts" / "preview.py"
SAMPLE = KIT / "samples" / "sample_grokbot_bot_activity.jsonl"


def main():
    result = subprocess.run(
        [sys.executable, str(PREVIEW), str(SAMPLE)],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(result.stdout)
    metrics = receipt["metrics"]
    token = urlsplit(receipt["preview_url"]).fragment.removeprefix("import=")
    imported = json.loads(base64.b64decode(unquote(token)))

    assert imported == metrics
    assert receipt["preview_url"].startswith(
        "https://agentic-strava.vercel.app/#import="
    )
    assert metrics["harness"] == "Grok Bot"
    assert metrics["activity_label"] == "bot activity"
    assert metrics["is_sample"] is True
    assert metrics["turns_typed"] == 2
    assert metrics["tool_calls"] == 3
    for field in ("duration_s", "ridge", "ridge_basis", "ridge_wall_seconds"):
        assert field not in metrics, f"fabricated {field}: {metrics[field]!r}"
    print("PASS: bundled sample produced a hosted preview with unknown duration and ridge.")


if __name__ == "__main__":
    main()
