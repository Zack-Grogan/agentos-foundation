# Use the template today

The complete local workflow needs **Python 3.11 or newer**, a browser and no account credentials. The application is for one trusted local user. The model provider is explicitly selected per job; no cloud service starts automatically.

## 1. Create your workspace

Use GitHub's **Use this template** and clone your new repository, or create a clean copy from this checkout:

```sh
python3 scripts/new_workspace.py ../my-agentos --name "My AgentOS" --profile research
cd ../my-agentos
python3 -m reference.cli init
python3 -m reference.cli doctor
python3 -m reference.server
```

Open **http://127.0.0.1:4321**. Ctrl-C stops the server and interrupts its active job. `--port` selects another explicit loopback address; `--data-dir` selects another private runtime directory.

Every profile keeps a central circle with layered orbits. Domain labels vary; click the center → Work view for the research workbench, operations board or monitoring records. A GitHub template clone uses the default orbital shell until you add a `workspace-profile.json` from `examples/` and customize its name.

## 2. Complete one job

Click **New capture**, enter a meaningful brief, and save it. In the source inspector:

- **Create plan draft** makes the small immediate deterministic example.
- **Run skill** queues a durable job using the selected provider (initially `local`). Open the job result when it succeeds.

Inspect the draft and its source. Accept its exact content as a local project, or reject it. Inside the project, record task progress. Acceptance and marking a task done do not execute external actions.

Open **All instruments → Memory** to search sources and accepted decisions. Editing a source creates a new revision; a decision derived from an older source revision is marked stale. Here current/stale describes revision agreement, not whether the evidence is recent enough for every domain.

## 3. Personalize the workspace

**All instruments** controls visibility, collapse, density, rail placement and order. Settings persist in the runtime database, with conflict detection between windows. Restore layout changes presentation only. The map stays anchored while app windows open. Draft capture text is browser-local and scoped to the workspace identity.

Use `.agents/skills/agentos-builder/SKILL.md` and fill `templates/product-brief.md` to replace the teaching domain with your own. Follow the app-shell and composer design contracts; do not turn the workspace into a website header/card/footer layout.

## 4. Run a local routine

Open a source and choose **Create routine**. Set an interval in seconds and a first-run ISO timestamp with timezone. A new routine is paused. Enable it deliberately.

Automatic ticking is a separate startup choice:

```sh
python3 -m reference.server --routines
```

This scheduler runs only while that process runs. It uses elapsed-time UTC intervals; missed intervals coalesce to the latest occurrence. It does not implement wall-clock cron or claim laptop-off operation. Pause cancels queued occurrences; use Stop job to cancel an already running job.

For a controlled command-line occurrence:

```sh
python3 -m reference.cli tick
python3 -m reference.cli work-once
```

## 5. Add your provider when ready

Follow [provider setup](provider-setup.md). Keep native subscription login in the user's own unmodified agent runtime. Direct model endpoints use explicitly configured API credentials. Static doctor results do not claim login or quota verification.

Provider configuration lives in ignored `.agentos/providers.json`. No automatic subscription-to-API fallback exists. Choose the configured instance in a source inspector's Run provider selector. Test one harmless selected input before enabling it on a routine.

## 6. Back up and restore

```sh
python3 -m reference.cli backup ../my-agentos-backup
python3 -m reference.cli restore ../my-agentos-backup ../my-agentos-restored-data
python3 -m reference.server --data-dir ../my-agentos-restored-data
```

Backup uses a consistent SQLite copy and checksums. Both destinations must be new. Restore verifies the copy before installing it, pauses routines and marks saved queued/running jobs interrupted. Native credential stores and provider workspace files are not part of the backup; the canonical database, identity marker and provider configuration are.

## Verify your copy

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check.py
python3 scripts/smoke_template.py
```

The fresh-copy acceptance script builds another temporary workspace and completes import → job → review → memory → routine → backup/restore using only shipped files. It creates no live provider session. For browser checks, use `npm ci --ignore-scripts`, `npx playwright install chromium`, then `npm run test:browser`.

For future updates, clone the newer upstream separately and run `python3 scripts/update_plan.py --upstream ../newer-foundation`. This produces a read-only three-way plan. Review and apply selected changes with your agent; it never overwrites your customizations automatically.
