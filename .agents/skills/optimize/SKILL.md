---
name: optimize
description: Improve responsiveness without hiding work or weakening truth.
---

Original AgentOS-specific procedure; not a vendored upstream skill.
Read [the spatial contract](../../../docs/design/spatial.md). Use [visual grammar](../../../docs/design/visual-grammar.md) for styling and [interactions](../../../docs/design/interactions.md) for behavior; load only the relevant reference.

1. Measure the actual slow action or rendering path before changing it.
2. Bound graph neighborhoods, lazy-load inspectors and avoid provider calls during render.
3. Verify interaction latency and unchanged data/failure semantics after the change.

Deliver changed artifacts or a concrete review with evidence. Preserve canonical state and permission boundaries. Do not make the screenshot more attractive by hiding real failures.
