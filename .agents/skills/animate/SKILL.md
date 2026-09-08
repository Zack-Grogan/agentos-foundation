---
name: animate
description: Add purposeful motion that explains workspace navigation and actual state changes.
---

Original AgentOS-specific procedure; not a vendored upstream skill.
Read [the spatial contract](../../../docs/design/spatial.md). Use [visual grammar](../../../docs/design/visual-grammar.md) for styling and [interactions](../../../docs/design/interactions.md) for behavior; load only the relevant reference.

1. Identify the relationship or transition motion must explain.
2. Use bounded transform/opacity movement and no fake activity or blocking delays.
3. Test interrupted transitions, focus continuity and reduced motion.

Deliver changed artifacts or a concrete review with evidence. Preserve canonical state and permission boundaries. Do not make the screenshot more attractive by hiding real failures.
