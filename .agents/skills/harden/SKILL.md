---
name: harden
description: Make workspace UI robust to missing data, large content and failed requests.
---

Original AgentOS-specific procedure; not a vendored upstream skill.
Read [the spatial contract](../../../docs/design/spatial.md). Use [visual grammar](../../../docs/design/visual-grammar.md) for styling and [interactions](../../../docs/design/interactions.md) for behavior; load only the relevant reference.

1. Exercise empty, stale, partial, blocked, failed and unknown states.
2. Preserve user drafts, selection and source context across errors.
3. Test long text, unavailable images, stale responses and safe rendering of untrusted input.

Deliver changed artifacts or a concrete review with evidence. Preserve canonical state and permission boundaries. Do not make the screenshot more attractive by hiding real failures.
