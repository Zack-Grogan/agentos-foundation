# Verification record — 0.2.0

Checked locally on 2026-09-08 against this template, not its source applications.

## Behavioral checks

`python3 -W error::ResourceWarning -m unittest discover -s tests -v`: **38 tests passed** on macOS / Python 3.14.

Coverage includes persisted capture/draft/review; duplicate and competing acceptance; source revisions and stale decisions; task status via the browser; explicit file import and symlink refusal; real child-process execution; configured HTTP and ACP peers through the complete job path; wall timeout and running cancellation; fenced result adoption; stale worker recovery; paused/due/coalesced interval routines; overlap and pause; persistent widget layout/CAS; old-schema migration; refusal of future/foreign schemas and missing databases; checksummed backup/restore with paused routines; manifest-based scaffolding, unrelated-file exclusion and read-only customization-preserving update planning; HTTP session/origin/CSRF/Host/path boundaries.

The provider peers are controlled fixtures. No live subscriber credentials or model usage were consumed.

## Fresh-copy acceptance

`python3 scripts/smoke_template.py`: passed. A new temporary copy runs the documented CLI sequence: init → doctor → explicit Markdown import → durable skill job → exact review → memory retrieval → enabled routine occurrence → duplicate trigger check → consistent backup → verified new-directory restore. Restored routines are paused. No original private files are imported.

This is an automated fresh-copy test, not a claimed independent fresh-LLM evaluation. The separate agent exercise is documented in `docs/skill-evaluation.md`.

## Browser

`npm run test:browser`: both suites passed in Chromium / Playwright 1.58.2.

The main app suite covers capture, review, accepted records, reload persistence, source rendering, layout recovery, keyboard focus, Escape, narrow layout and reduced motion. App-shell assertions require no website footer, a header no taller than 56px, equal rails and an unchanged viewport-centered map when app windows open.

The second suite creates **three fresh template copies**, selects three domain profiles with a shared orbital shell and contextual work views, completes durable jobs and review, changes a task's status, searches memory, persists collapse/restore and checks 390px layout. JavaScript page errors: zero. Rendered profile screenshots were inspected; all input is synthetic.

Regenerate images explicitly with `UPDATE_SCREENSHOTS=1 npm run test:browser`. Normal test runs do not overwrite committed screenshots.

## Repository checks

`python3 scripts/check.py`: local links, skill metadata, JSON, disabled provider/routine templates and export boundaries. `python3 scripts/check.py --strict-template` additionally compares the reviewed distribution manifest with actual file hashes. Draft 2020-12 schema meta-validation was performed for the original architectural contracts. Ruff undefined/unused-code checks pass.

GitHub CI repeats Python 3.11/3.14 checks, fresh-copy acceptance and both browser suites on Linux. Read the live Actions result for the published commit; do not infer it from this local record.

## Scope

Ready for a single-user trusted local workspace with deterministic operation and opt-in text-plan providers. Full conversational streaming/voice, provider-specific extension UIs, client tool grants, cron/DST scheduling, laptop-off hosting, multi-user access and a general external-action executor remain deliberate extensions. Native account entitlement and confinement require the user's own provider setup and a real scoped run. The local template's tests do not establish those account-specific facts.
