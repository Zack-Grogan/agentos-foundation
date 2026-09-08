# Local AgentOS runtime

Start with [the quickstart](../docs/quickstart.md). Python 3.11+; no third-party runtime dependency.

- `core.py`, `validation.py`, `schema.py`: source revisions, plan validation, review, task progress and versioned storage.
- `jobs.py`, `runner.py`, `provider_worker.py`: durable queue, one active owner, bounded child process, cancellation and fenced result adoption.
- `providers.py`: explicit workspace instances and static diagnostics; credentials are references, not values in configuration.
- `memory.py`: search over sources and accepted decisions with current/stale evidence status.
- `layout.py`, `profile.py`: persistent widget registry and a shared orbital center and profile-specific contextual work views.
- `recovery.py`, `cli.py`: explicit local file import, initialization, jobs/routines and checksummed backup/restore.
- `server.py`, `web/`: loopback named operations and the app shell. UI and CLI share the same domain services.

The default provider produces a deterministic plan. Configured ACP and HTTP providers return the same validated text-plan contract. Job results are drafts; only explicit review creates projects. Task status records user progress and does not execute external work.

Run `python3 -m reference.server`. Add `--routines` only to tick explicitly enabled UTC interval routines. Routine definitions are paused by default. The server processes queued jobs in a bounded child while remaining available for browsing and Stop requests.

Data lives in ignored `.agentos/`. Layout is persisted in SQLite; capture drafts remain browser-local and workspace-scoped. Provider native credentials are user-owned and never copied by the runtime. On restore, active/queued jobs are interrupted and routines are paused.

This is a one-user trusted loopback application. It does not provide multi-user identity, public deployment, a full conversational composer, provider-specific extension UIs or a general external tool executor. Read [readiness](../docs/readiness.md) before widening the scope.
