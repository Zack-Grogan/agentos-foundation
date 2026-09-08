# Working reference

A deliberately small, dependency-free implementation of one ARMS loop. `core.py` owns canonical sources, runs, artifacts, reviews and accepted projects. `server.py` exposes named operations and allowlisted assets. `web/` projects real records as a spatial workspace.

`python3 -m reference.server` starts at `http://127.0.0.1:4321`. Use Python 3.11+. Capture a brief; generate its deterministic draft; inspect source and run provenance; accept or reject. Repeated identical request IDs return the same result. Acceptance is digest-bound and creates one local project. A rejected draft remains visible.

The local planner copies the objective and adds an explicitly generic three-step scaffold. It does not analyze meaning or call a model. Runs complete synchronously, so no fictional streaming progress or Stop button is shown. The reference has no scheduler or application connector; their requirements live in the playbook. “Accepted” means adopted into local project records, not external execution.

Storage: ignored `.agentos/workspace.sqlite3`. Layout mode, instrument visibility and order are browser-local preferences. Runtime records survive restart; layout is disposable. The server accepts only the exact loopback origin, bootstraps a same-origin local session, checks CSRF on writes and never serves the data directory. Any process on the same machine remains within the local trust boundary. This server is not intended for exposure to other users or networks.

Replace the planner behind the domain service with an authorized adapter; add durable queued execution, cancellation and budget enforcement before making long-running model calls. Keep source, artifact and review identities intact. See `docs/architecture.md` for extension contracts.
