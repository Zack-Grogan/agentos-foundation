"""Searchable projections of canonical evidence; revalidate accepted claims each read."""

import re
from .core import digest


def entries(store, query=""):
    state = store.snapshot()
    sources = {s["id"]: s for s in state["sources"]}
    rows = []
    for source in sources.values():
        rows.append(
            {
                "id": source["id"],
                "kind": "source",
                "title": source["title"],
                "text": source["body"],
                "source_id": source["id"],
                "status": "observed",
                "observed_at": source["observed_at"],
            }
        )
    for artifact in state["artifacts"]:
        if artifact["review"] != "accepted":
            continue
        source = sources.get(artifact["content"]["source_id"])
        fresh = bool(
            source
            and source["digest"] == artifact["content"]["source_digest"]
            and digest(artifact["content"]) == artifact["digest"]
        )
        rows.append(
            {
                "id": artifact["id"],
                "kind": "decision",
                "title": artifact["content"]["title"],
                "text": artifact["content"]["objective"],
                "source_id": artifact["content"]["source_id"],
                "status": "current" if fresh else "stale",
                "observed_at": artifact["created_at"],
            }
        )
    terms = re.findall(r"\w+", query.lower())
    return [
        r
        for r in rows
        if all(t in (r["title"] + " " + r["text"]).lower() for t in terms)
    ][:100]
