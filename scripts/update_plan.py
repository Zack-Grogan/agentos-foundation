"""Read-only three-way template update planning; never overwrites customization."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file() and not path.is_symlink()
        else None
    )


def plan(workspace, upstream):
    workspace, upstream = Path(workspace).resolve(), Path(upstream).resolve()
    baseline = json.loads((workspace / ".foundation-baseline.json").read_text())
    proposed = json.loads((upstream / "template-manifest.json").read_text())
    rows = []
    for name in sorted(set(baseline["files"]) | set(proposed["files"])):
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe manifest path.")
        if (
            any(p.is_symlink() for p in [workspace / rel, upstream / rel])
            or workspace not in (workspace / rel).resolve().parents
            or upstream not in (upstream / rel).resolve().parents
        ):
            raise ValueError("Escaping update path.")
        old = baseline["files"].get(name)
        local = digest(workspace / rel)
        new = digest(upstream / rel) if name in proposed["files"] else None
        if name == "template-manifest.json":
            continue
        if local == new:
            status = "same"
        elif old == new:
            status = "local-customization"
        elif old is None:
            status = "add" if local is None else "conflict"
        elif new is None:
            status = "upstream-removed-review-required"
        elif local == old:
            status = "upstream-update"
        else:
            status = "conflict"
        if status != "same":
            rows.append({"path": name, "status": status})
    return {
        "mode": "read-only",
        "from_version": baseline["template_version"],
        "to_version": proposed["version"],
        "changes": rows,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, default=Path("."))
    p.add_argument("--upstream", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(plan(args.workspace, args.upstream), indent=2))
