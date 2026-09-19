"""Run the installed STRIVE Grok kit against its bundled labelled sample."""
import base64
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
    for field in ("duration_s", "ridge_wall_seconds"):
        assert field not in metrics, f"fabricated {field}: {metrics[field]!r}"
    assert metrics["ridge_basis"] == "turn-order"
    assert len(metrics["ridge"]) == 50
    assert sum(metrics["ridge"]) == metrics["tool_calls"]
    print("PASS: bundled sample produced a measured turn-order ridge without a duration claim.")

    # The upload helper refuses the sample and sends nothing without a token.
    upload = subprocess.run(
        [sys.executable, str(KIT / "scripts" / "upload.py"), str(SAMPLE), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert upload.returncode == 1 and "bundled sample" in upload.stdout, upload.stdout
    print("PASS: upload helper refuses the bundled sample.")
    upload_boundary()


def serve(handler_body):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            seen.append(self.headers.get("Authorization"))
            handler_body(self)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, seen


def reply(status, body=b"", location=None):
    def send(h):
        h.send_response(status)
        if location:
            h.send_header("Location", location)
        h.send_header("Content-Type", "application/json")
        h.end_headers()
        h.wfile.write(body)
    return send


def upload_boundary():
    # A real-looking export: the sample without its sample marker. Local synthetic servers only.
    rows = [json.loads(line) for line in SAMPLE.read_text().splitlines() if line.strip()]
    for row in rows:
        row.pop("agentgrinder_sample", None)
    export = Path(tempfile.mkdtemp()) / "export.jsonl"
    export.write_text("".join(json.dumps(r) + "\n" for r in rows))
    env = dict(os.environ, STRIVE_AGENT_TOKEN="ag_synthetic-test-token")

    def run(server):
        return subprocess.run(
            [sys.executable, str(KIT / "scripts" / "upload.py"), str(export),
             "--base-url", f"http://127.0.0.1:{server.server_port}"],
            capture_output=True, text=True, env=env)

    elsewhere, elsewhere_seen = serve(reply(200, b'{}'))
    redirect, _ = serve(reply(307, location=f"http://localhost:{elsewhere.server_port}/steal"))
    out = run(redirect)
    assert out.returncode == 1 and "redirect" in out.stdout, out.stdout
    assert elsewhere_seen == [], "the bearer token was resent after a redirect"

    empty, _ = serve(reply(200, b"{}"))
    out = run(empty)
    assert out.returncode == 1 and '"unknown"' in out.stdout, out.stdout

    good, seen = serve(reply(200, json.dumps({"id": "00000000-0000-0000-0000-000000000099",
                                               "visibility": "private", "existing": True}).encode()))
    out = run(good)
    result = json.loads(out.stdout)
    assert out.returncode == 0 and result["status"] == "already saved" and result["visibility"] == "private", out.stdout
    assert seen == ["Bearer ag_synthetic-test-token"]
    assert "ag_synthetic" not in out.stdout, "the token is never printed"
    for server in (elsewhere, redirect, empty, good):
        server.shutdown()
    print("PASS: upload never follows a redirect with the token and needs a real stored result.")


if __name__ == "__main__":
    main()
