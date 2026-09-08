"""Check local documentation links, skill metadata and public export boundaries."""

import hashlib
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".agentos",
    "node_modules",
    "__pycache__",
    "test-results",
    "private",
    ".ruff_cache",
    "backups",
}
errors = []
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and not any(x in SKIP for x in p.relative_to(ROOT).parts)
]
for path in files:
    rel = path.relative_to(ROOT)
    if path.suffix == ".json":
        try:
            json.loads(path.read_text())
        except ValueError as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
    if path.suffix == ".md":
        text = path.read_text()
        for link in re.findall(r"\]\(([^)]+)\)", text):
            link = link.split("#")[0]
            if not link or "://" in link or link.startswith("mailto:"):
                continue
            if not (path.parent / link).resolve().exists():
                errors.append(f"{rel}: broken link {link}")
        if path.name == "SKILL.md":
            if not text.startswith("---\n") or not re.search(
                r"^description: .+", text, re.M
            ):
                errors.append(f"{rel}: missing skill metadata")
            if f"name: {path.parent.name}\n" not in text:
                errors.append(f"{rel}: skill name mismatch")
        if "/Users/" in text or "/home/debian/" in text:
            errors.append(f"{rel}: personal machine path")
    if path.name.startswith(".env") and path.name != ".env.example":
        errors.append(f"{rel}: environment file in export")
    if path.suffix.lower() in (".pdf", ".sqlite3", ".jsonl"):
        errors.append(f"{rel}: unexpected source/runtime artifact")
providers = json.loads((ROOT / "templates/providers.json").read_text())
if providers["automatic_billing_fallback"] or any(
    x["enabled"] for x in providers["instances"]
):
    errors.append("Provider template must stay opt-in")
if json.loads((ROOT / "templates/routine.json").read_text())["enabled"]:
    errors.append("Routine template must be disabled")
runtime = json.loads((ROOT / "templates/runtime-providers.json").read_text())
if any(x["enabled"] for x in runtime["instances"]):
    errors.append("Runtime providers must ship disabled")
if "--strict-template" in sys.argv:
    release = json.loads((ROOT / "template-manifest.json").read_text())
    for name, expected in release["files"].items():
        p = ROOT / name
        if (
            p.is_symlink()
            or not p.is_file()
            or ROOT not in p.resolve().parents
            or hashlib.sha256(p.read_bytes()).hexdigest() != expected
        ):
            errors.append("Release manifest mismatch: " + name)
if errors:
    raise SystemExit("\n".join(errors))
print(
    f"Checked {len(files)} public files; {len(list((ROOT / '.agents/skills').glob('*/SKILL.md')))} skill entry points; links, JSON and export boundaries pass."
)
