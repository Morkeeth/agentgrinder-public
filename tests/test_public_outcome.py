import subprocess, sys, pathlib


def test_public_share_page_renders_declared_receipts_safely():
    probe = pathlib.Path(__file__).parent / "fixtures" / "public_outcome_probe.mjs"
    result = subprocess.run(["node", str(probe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS public share page" in result.stdout
