"""Fresh-copy acceptance with only shipped code, examples and documented CLI commands."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from new_workspace import create


def call(root, *args):
    result = subprocess.run(
        [sys.executable, "-m", "reference.cli", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


with tempfile.TemporaryDirectory(prefix="agentos-fresh-copy-") as directory:
    root = create(Path(directory) / "workspace", "Fresh research studio", "research")
    call(root, "init")
    doctor = call(root, "doctor")
    assert doctor["instances"][0]["status"] == "ready-local"
    source = call(root, "import", "examples/worked/research/input.md")
    job = call(root, "run", source["id"], "--request-id", "fresh-run")
    assert job["status"] == "succeeded", job
    state = call(root, "status")
    artifact = state["records"]["artifacts"][0]
    call(
        root,
        "review",
        artifact["id"],
        "--digest",
        artifact["digest"],
        "--decision",
        "accepted",
    )
    assert any(x["kind"] == "decision" for x in call(root, "memory", "research"))
    routine = call(
        root,
        "routine-create",
        source["id"],
        "--interval",
        "60",
        "--first-run",
        "2026-01-01T00:00:00Z",
    )
    call(root, "routine-enable", routine["id"], "--revision", "1")
    assert len(call(root, "tick", "--at", "2026-01-01T00:03:00Z")) == 1
    assert call(root, "work-once")["status"] == "succeeded"
    assert call(root, "tick", "--at", "2026-01-01T00:03:00Z") == []
    backup = Path(directory) / "backup"
    restored = Path(directory) / "restored"
    call(root, "backup", str(backup))
    call(root, "restore", str(backup), str(restored))
    result = subprocess.run(
        [sys.executable, "-m", "reference.cli", "--data-dir", str(restored), "status"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    restored_state = json.loads(result.stdout)
    assert len(restored_state["records"]["projects"]) == 1
    assert restored_state["routines"][0]["enabled"] is False
    assert not (root / ".git").exists()
print(
    "Fresh-template acceptance passed: scaffold, initialize, doctor, import, durable run, review, memory, routine, duplicate trigger, backup and restore."
)
