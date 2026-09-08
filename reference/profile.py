"""Small validated domain profile; explicit choice changes the reference composition."""

import json
from pathlib import Path
from .core import Invalid


def profile(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    path = root / "workspace-profile.json"
    if not path.exists():
        return {
            "name": "Work studio",
            "profile": "monitoring",
            "composition": "orbital",
            "detail_view": "anchored-map",
            "objects": ["Sources", "Drafts", "Projects", "Runs"],
        }
    if path.is_symlink() or path.stat().st_size > 10000:
        raise Invalid("Invalid workspace profile file.")
    value = json.loads(path.read_text())
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("name"), str)
        or not 1 <= len(value["name"]) <= 120
    ):
        raise Invalid("Profile name is required.")
    detail = value.get("detail_view", value.get("composition"))
    if detail not in ("workbench", "board", "anchored-map"):
        raise Invalid("Unknown detail view.")
    return {**value, "composition": "orbital", "detail_view": detail}
