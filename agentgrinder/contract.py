"""Versioned exchange contract. Private transcript metadata is never an export field."""
from __future__ import annotations

import hashlib
import math

SCHEMA_VERSION = 1
COUNT_FIELDS = ("turns_typed", "tool_calls", "shell_calls", "files_touched", "commits", "claims",
                "claims_verified", "artifacts_produced")


def validate_run(run: dict) -> dict:
    if not isinstance(run, dict):
        raise ValueError("A grind must be a JSON object.")
    version = run.get("schema_version", 0)
    if type(version) is not int or version not in (0, SCHEMA_VERSION):
        raise ValueError("This grind uses an unsupported format. Update Agent Grinder to read it.")
    for name in COUNT_FIELDS:
        value = run.get(name)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"{name} must be a non-negative whole number or unknown.")
    duration = run.get("duration_s")
    if duration is not None and (type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0):
        raise ValueError("duration_s must be a finite non-negative number or unknown.")
    claims, verified = run.get("claims"), run.get("claims_verified")
    if verified is not None and claims is None:
        raise ValueError("Verified claims require a counted-claims total.")
    if claims is not None and verified is not None and verified > claims:
        raise ValueError("Verified claims cannot exceed the claims counted.")
    ridge = run.get("ridge")
    if ridge is not None:
        if (not isinstance(ridge, list) or not 40 <= len(ridge) <= 60
                or any(type(value) is not int or value < 0 for value in ridge)):
            raise ValueError("ridge must contain 40 to 60 non-negative whole-number bins.")
        workers = run.get("worker_bins")
        if (not isinstance(workers, list) or len(workers) != len(ridge)
                or any(type(value) is not int or value < 0 for value in workers)):
            run["worker_bins"] = [0] * len(ridge)
        commits = run.get("commit_bins", [])
        if (not isinstance(commits, list)
                or any(type(value) is not int or value < 0 or value >= len(ridge)
                       for value in commits)):
            raise ValueError("commit_bins must contain valid ridge bin indexes.")
        if run.get("ridge_basis") not in ("wall-time", "call-index", "turn-order"):
            raise ValueError("ridge_basis must be wall-time, call-index, or turn-order.")
        wall = run.get("ridge_wall_seconds")
        if (wall is not None
                and (type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0)):
            raise ValueError("ridge_wall_seconds must be a finite non-negative number or unknown.")
        # The store's own count. It is recorded next to tool_calls, never compared against it.
        store_calls = run.get("ridge_tool_calls")
        if store_calls is not None and (type(store_calls) is not int or store_calls < 0):
            raise ValueError("ridge_tool_calls must be a non-negative whole number or unknown.")
    return run


def public_revision(run: dict) -> dict:
    """Only opaque revision references travel; paths, source digests and commands stay local."""
    measurement = run.get("measurement") or {}
    out = {"schema_version": SCHEMA_VERSION}
    for source, target in (("revision_id", "measurement_revision"),
                           ("baseline_revision_id", "baseline_revision")):
        value = measurement.get(source, run.get(target))
        if value is not None:
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("Invalid measurement revision reference.")
            out[target] = value
    return out


def capture_digest(path) -> str:
    """Hash the actual transcript bytes locally, without retaining a second transcript copy."""
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
