# Running and recovering an AgentOS

## Local reference

Run `python3 -m reference.server`, open `http://127.0.0.1:4321`, stop with Ctrl-C. Use `--port` for an explicit alternate address and `--data-dir` for an isolated workspace. Runtime data lives in `.agentos/workspace.sqlite3`; UI preferences are browser-local and disposable. Deleting browser preferences must never delete domain records.

For backup, stop the process and copy the entire data directory to a private destination. Restore to a new directory, start with `--data-dir`, and compare sources, drafts, review states, events and accepted projects. Keep the original until the restored copy is verified. No deletion is required to restore. For a running production SQLite app, use its backup API rather than copying an active DB file.

## Routine runbook contract

Record the trigger timezone, intended occurrence, maximum lateness, missed-run policy (`skip`, `latest`, or bounded `catch_up`), concurrency key, deadline, attempts, input revision, output destination and notification policy. Specify DST gap/fold behavior. A sensible initial policy is skip nonexistent local times and run an ambiguous occurrence once. Test the selected policy against a real timezone transition.

Pause blocks new claims. Stop requests cancellation for an active run. Neither undoes an already confirmed external action. Shutdown should release resources and mark unfinished local work interrupted; an uncertain external effect stays unknown pending reconciliation. Expired claims require fencing before a new worker resumes.

## Failure ownership

| Failure | Required next step |
| --- | --- |
| Authentication revoked | Block the capability; show the owner how to reconnect without printing secrets |
| Missing or stale source | Identify the source and refresh path; do not substitute an old result silently |
| Rate/usage limit | Record measured limit evidence; pause or bounded retry according to policy |
| Output validation failure | Preserve evidence for review; do not publish or promote to memory |
| Lost external response | Reconcile stable request identity; do not create a replacement action |
| Corrupt runtime storage | Stop writes, preserve files and restore to a new location |
| Layout schema change | Migrate presentation state or reset layout explicitly; preserve domain records |

## Hosted extension

Only add hosting when required. This template does not deploy infrastructure. For an authorized deployment, Railway is the default operational choice unless the owner selects another provider; use its current official CLI/docs. Add identity, per-operation authorization, TLS, tenant boundaries where applicable, secret storage, backup restoration, process supervision and deployment verification first.

A remote worker uses a dedicated checkout and reviewed code/config revisions. Sync only selected non-code artifacts with exclusions and conflict ownership. Do not synchronize a live database, authentication folder, dependency tree or concurrently edited checkout as a reliability strategy.

## Observability

Persist structured events with run IDs, safe error codes and source/output references. Keep raw model prompts, provider responses and private data out of public logs. Measure scheduling delay, run duration, validation failures, review outcomes and output delivery when available. Distinguish measured usage from estimates. Alerts need an owner and an actual recovery action.
