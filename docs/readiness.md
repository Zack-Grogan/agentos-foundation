# Template readiness boundary

This release is ready to clone and use for a **single-user local AgentOS** with a complete deterministic workflow and opt-in configured text providers. Readiness is tested against the shipped scope, not a promise that every account, operating system or future customization is bug-free.

| Capability | Shipped behavior | Verification |
| --- | --- | --- |
| Scaffold | Reviewed-file allowlist, profile selection, baseline hashes, no overwrite | Fresh-copy acceptance and private-file exclusion |
| Source application | UI capture and explicit local Markdown/text import | Duplicate and symlink tests |
| Skills | Named capture-to-plan plus project instruction library and worked fixtures | Normal/incomplete input and output-shape tests |
| Provider jobs | Durable queue, one owner, deadlines, cancel, changed-source/config fence | Child process, HTTP peer and ACP peer tests |
| Review | Digest/source-bound adoption and task progress | Repeated/concurrent review and stale edits |
| Memory | Search over sources and accepted decisions; stale-source marking | Source edit and retrieval tests |
| Routines | Paused by default; explicit UTC intervals; latest missed occurrence; no overlap | Due/duplicate/pause tests and fresh-copy execution |
| Widget/app shell | Server-persisted registry layout; hide/restore/collapse/density/order/rail | CAS and browser controls |
| Design profiles | Shared central circle and layered orbits; profile-specific labels and contextual work views | Browser workflow and profile renders |
| Recovery | Additive schema migration, pre-migration copy, checksummed consistent backup, new-directory restore | Old schema, future/foreign DB refusal, corrupt backup and restart tests |
| Updates | Read-only three-way comparison preserving local edits | Customized-copy tests |

Deliberate extensions: a full streaming conversational composer, native provider extension UIs, client tool grants, cron/DST schedules, laptop-off hosting, multi-user identity, and unrestricted external action execution. These have design/architecture contracts but are not required to start using this local template.

Live subscriber sessions are account-specific setup, not a universal verified property of the public repository. Test your chosen instance once before enabling it on a routine. The shipped peer tests prove the transport and integration path without consuming a subscription.
