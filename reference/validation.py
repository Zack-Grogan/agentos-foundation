"""Strict boundary for model-produced plans; sources are attached by the server."""

from .core import Invalid, bounded


def validate_plan(value):
    keys = {"title", "objective", "assumptions", "questions", "next_actions"}
    if not isinstance(value, dict) or set(value) != keys:
        raise Invalid(
            "Plan must have exactly title, objective, assumptions, questions and next_actions."
        )
    result = {
        "title": bounded(value["title"], "Plan title", 120),
        "objective": bounded(value["objective"], "Plan objective", 12000),
    }
    for key in ("assumptions", "questions", "next_actions"):
        rows = value[key]
        if (
            not isinstance(rows, list)
            or len(rows) > 20
            or (key == "next_actions" and not rows)
        ):
            raise Invalid(f"Invalid {key} list.")
        result[key] = [bounded(row, key, 1000) for row in rows]
    return result
