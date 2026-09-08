"""Copy only the published template manifest into a new independent workspace."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath


def manifest(root):
    value = json.loads((root / "template-manifest.json").read_text())
    if value.get("format") != 1 or not isinstance(value.get("files"), dict):
        raise ValueError("Invalid template manifest.")
    for name in value["files"]:
        rel = PurePosixPath(name)
        if (
            rel.is_absolute()
            or ".." in rel.parts
            or not rel.parts
            or any(
                x in (".git", ".agentos", "private", "node_modules") for x in rel.parts
            )
        ):
            raise ValueError("Unsafe manifest path.")
        path = root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or root.resolve() not in path.resolve().parents
        ):
            raise ValueError("Missing or escaping template file: " + name)
    return value


def create(destination, name, profile):
    root = Path(__file__).resolve().parents[1]
    destination = Path(destination)
    if destination.is_symlink() or destination.exists():
        raise ValueError("Choose a new destination; nothing will be overwritten.")
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("Choose a destination outside the template.")
    if profile not in ("research", "operations", "monitoring"):
        raise ValueError("Unknown domain profile.")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("Name must contain 1–120 characters.")
    value = manifest(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".agentos-scaffold-", dir=destination.parent))
    try:
        hashes = {}
        for rel in [*value["files"], "template-manifest.json"]:
            path = temp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / rel, path)
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        data = json.loads((root / "examples" / f"{profile}.json").read_text())
        data["name"] = name.strip()
        (temp / "workspace-profile.json").write_text(json.dumps(data, indent=2) + "\n")
        (temp / ".foundation-baseline.json").write_text(
            json.dumps(
                {"format": 1, "template_version": value["version"], "files": hashes},
                indent=2,
            )
            + "\n"
        )
        os.rename(temp, destination)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--profile",
        choices=("research", "operations", "monitoring"),
        default="operations",
    )
    args = parser.parse_args()
    try:
        target = create(args.destination, args.name, args.profile)
    except ValueError as exc:
        parser.error(str(exc))
    print(
        f"Created {target}. Start with docs/quickstart.md; the selected profile controls the workspace composition."
    )
