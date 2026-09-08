"""Server-persisted presentation preferences with optimistic concurrency."""

import json
from .core import Invalid, Conflict

REGISTRY = [
    {
        "id": "sources-panel",
        "title": "Source library",
        "rail": "left",
        "order": 0,
        "visible": True,
        "collapsed": False,
        "density": "comfortable",
        "app": "sources",
    },
    {
        "id": "procedure-panel",
        "title": "Procedure",
        "rail": "left",
        "order": 1,
        "visible": True,
        "collapsed": False,
        "density": "comfortable",
        "app": "jobs",
    },
    {
        "id": "review-widget",
        "title": "Review queue",
        "rail": "right",
        "order": 0,
        "visible": True,
        "collapsed": False,
        "density": "comfortable",
        "app": "artifacts",
    },
    {
        "id": "activity-panel",
        "title": "Recent activity",
        "rail": "right",
        "order": 1,
        "visible": True,
        "collapsed": False,
        "density": "comfortable",
        "app": "runs",
    },
]


def read_layout(store):
    with store.connect() as db:
        row = db.execute("SELECT body FROM settings WHERE key='layout'").fetchone()
    return (
        json.loads(row[0])
        if row
        else {"revision": 1, "mode": "map", "widgets": [dict(x) for x in REGISTRY]}
    )


def save_layout(store, layout):
    if (
        not isinstance(layout, dict)
        or set(layout) != {"revision", "mode", "widgets"}
        or type(layout["revision"]) is not int
    ):
        raise Invalid("Invalid layout document.")
    if layout["mode"] not in ("map", "list") or not isinstance(layout["widgets"], list):
        raise Invalid("Invalid view mode or widget list.")
    widgets = layout["widgets"]
    if len(widgets) != len(REGISTRY) or {
        w.get("id") for w in widgets if isinstance(w, dict)
    } != {w["id"] for w in REGISTRY}:
        raise Invalid(
            "Keep every registered widget exactly once; use visible=false to hide."
        )
    for w in widgets:
        template = next(r for r in REGISTRY if r["id"] == w["id"])
        if (
            set(w) != set(template)
            or w["title"] != template["title"]
            or w["app"] != template["app"]
        ):
            raise Invalid("Widget identity cannot be changed by layout.")
        if (
            w["rail"] not in ("left", "right")
            or type(w["order"]) is not int
            or not 0 <= w["order"] < len(REGISTRY)
        ):
            raise Invalid("Invalid widget position.")
        if (
            type(w["visible"]) is not bool
            or type(w["collapsed"]) is not bool
            or w["density"] not in ("compact", "comfortable")
        ):
            raise Invalid("Invalid widget presentation.")
    if len({(w["rail"], w["order"]) for w in widgets}) != len(widgets):
        raise Invalid("Widget positions must be unique per rail.")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT body FROM settings WHERE key='layout'").fetchone()
        revision = json.loads(row[0])["revision"] if row else 1
        if revision != layout["revision"]:
            raise Conflict("Layout changed in another window; refresh and try again.")
        result = {**layout, "revision": revision + 1}
        db.execute(
            "INSERT OR REPLACE INTO settings VALUES ('layout',?)", (json.dumps(result),)
        )
        return result
