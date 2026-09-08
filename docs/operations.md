# Running and recovering an AgentOS

## Local reference

Run `python3 -m reference.server`, open `http://127.0.0.1:4321`, stop with Ctrl-C. Use `--port` for an explicit alternate address and `--data-dir` for an isolated workspace. Runtime data lives in `.agentos/workspace.sqlite3`; Widget layout persists in SQLite; capture text drafts are browser-local and disposable. Deleting browser preferences must never delete domain records.

Use `python3 -m reference.cli backup ../new-backup` for a consistent database copy and checksum manifest. Restore with `python3 -m reference.cli restore ../new-backup ../new-restored-data`, then start with that `--data-dir`. Existing destinations are refused. Restore pauses routines and interrupts saved jobs; native account profiles are not backed up. See [quickstart](quickstart.md) for exact steps.

The shipped scheduler uses UTC elapsed-time intervals and latest-occurrence coalescing. The following cron/DST discussion is the extension contract for a future wall-clock scheduler, not a claim of current cron support.

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
