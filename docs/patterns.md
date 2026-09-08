# Patterns extracted from existing work

Reviewed source on 2026-09-08. This is an architectural reading, not a new test run of either source application. Source fingerprints are in `source-manifest.json`. G-Portfolio had no commit at review time, so filenames and SHA-256 digests identify the examined snapshot. No private source tree is vendored.

| Source area | Observed pattern | Generalization | Do not copy blindly |
| --- | --- | --- | --- |
| G-Portfolio `apps/core/workspace.py` | Read-only presentation over stored records; stable domain node coordinates; news tied to objects | Build a projection over canonical data; let inspectors provide contextual evidence | Asset names, allocations and radial arrangement are domain-specific |
| `static/workspace.js` | Overlay navigation, request cancellation/versioning, restoration of tabs/scroll, explicit uncertain-submit wording | Keep object context across detail navigation; stale response cannot replace newer view | HTML fragment handling is not a universal sanitizer |
| `.impeccable.md` | Center remains stable; warm restrained instruments; corner chat; no invented metrics | Write durable composition rules before styling | This palette and circle map are an example, not the only AgentOS design |
| `apps/assistant/memory.py` | Pinned memory checked against source digests | Evidence-derived memory must be revalidated when sources change | A pin alone is not universal verification; freshness/deletion need their own policy |
| `apps/assistant/skills.py` | Project allowlist and refused capabilities | Skill discovery is controlled and scoped | Text keyword refusal and an 8k cutoff are not a sandbox or complete skill packaging |
| `apps/routines/scheduler.py` | DST policy, occurrence identity, revisions, coalescing | Make schedule semantics explicit and bounded | Choose missed-run policy per job |
| `apps/routines/worker.py` | Role gate, lease token, renewal, revision checks and bounded attempts | Separate claiming, doing work and fenced finalization | Production locking must be tested on the actual DB |
| `apps/desk/execution.py`, `tests/coinbase/test_live_lifecycle.py` | Named execution role and durable order lifecycle call path | Keep external execution separate from planning; preserve request identity | A financial workflow is not included in this generic reference |
| `tests/assistant/test_conversation_stream.py` | Duplicate turn prevention, partial reply preservation, disconnect/stop distinctions | Build composer behavior around persisted events | Streaming UI alone cannot prove cancellation |
| `apps/core/auth.py` | Direct local peer/Host checks and separate shared-access path | Local-only is a deliberate boundary | It is not multi-user authentication |
| Earlier AgentOS `src/shared/layout.ts`, `src/server/layout.ts` | Stable widget IDs, bounded sizes and layout revision checks | Persist presentation separately and reject stale edits | Server-local layout persistence is distinct from cross-device synchronization |
| Earlier AgentOS project skill | Capture produces a sourced plan draft without activation | First loop should end at a reviewable artifact | This repo provides an original implementation rather than copying the app |

## Conversation-derived product intent

The reviewed AgentOS conversation replaced page/sidebar navigation with a unified widget/app workspace and made chat secondary. G-Portfolio conversations emphasized object-specific news, an in-app reader, meaningful filter differences, stable return context and distinct price versus position values. Composer planning called for draft persistence, real streaming and stop semantics, plus explicit voice activation.

These are product decisions and historical observations, not current runtime facts. Private transcripts, voice content, balances, identifiers and screenshots were excluded from the public repository. Earlier completion claims and test totals were not adopted as proof for this foundation.

## Lessons beyond the happy path

A status label can disagree with its implementation. A web process can run while workers are absent. A refresh can return cached data without producing a new snapshot. A SQLite test may miss PostgreSQL locking behavior. A provider can exceed a requested tool budget. Therefore check evidence at the actual boundary, expose partial states and put hard controls outside model prose.
