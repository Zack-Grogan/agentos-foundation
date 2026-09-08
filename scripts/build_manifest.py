"""Maintainer-only: build the distributable allowlist from reviewed staged Git paths."""

import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = (
    subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
)
files = {}
for name in paths:
    if not name or name == "template-manifest.json":
        continue
    p = root / name
    if (
        p.is_symlink()
        or any(
            x in (".agentos", "private", "node_modules", ".git")
            for x in p.relative_to(root).parts
        )
        or p.name.startswith(".env")
        or p.suffix in (".sqlite3", ".bak", ".pdf")
    ):
        raise SystemExit("Unsafe export path: " + name)
    files[name] = hashlib.sha256(p.read_bytes()).hexdigest()
(root / "template-manifest.json").write_text(
    json.dumps({"format": 1, "version": "0.2.0", "files": files}, indent=2) + "\n"
)
print(f"Built reviewed allowlist for {len(files)} files.")
