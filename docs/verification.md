# Verification record

Checked locally on 2026-09-08. This record concerns **agentos-foundation**, not the source applications used for inspiration.

## Automated behavior

`python3 -W error::ResourceWarning -m unittest discover -s tests -v`: **21 tests passed**, Python 3.14 on macOS.

Covered: full persisted local workflow; duplicate capture/draft and repeated/competing review; stale/tampered artifact and changed source; failed validation; rejected draft; incomplete input; backup restore; HTTP origin, session and CSRF boundary; Host/proxy rejection; named asset/operation allowlist; untrusted text as data; scaffold isolation/no overwrite; three endpoint request/response dialects; an actual local HTTP peer and redirect rejection; actual ACP subprocess initialization, streamed update, permission denial, cancellation, timeout and malformed peer.

## Browser

`npm ci --ignore-scripts`, `npx playwright install chromium`, `npm run test:browser`.

Passed in headless Chromium with Playwright 1.58.2. The test starts its own temporary loopback server and isolated database, then closes them. It covers capture, draft, explicit acceptance, opening the accepted project, refresh persistence, hide/restore and list/map preferences, capture draft recovery, inert malicious source text, modal focus containment, Escape/focus return, 390px layout without horizontal overflow, and reduced-motion mode. JavaScript page errors: zero.

App-shell checks verify a header no taller than 56px, no conventional footer, equal-width rails, and an unchanged viewport-centered anchor when capture/inspectors open.

Rendered desktop (1440px) and narrow (390px) screenshots were visually inspected. All shown records are labeled synthetic inputs produced by the test workflow. To deliberately update the images: `UPDATE_SCREENSHOTS=1 npm run test:browser`.

## Repository checks

`python3 scripts/check.py` validates local Markdown links, skill metadata, JSON parsing and key public-export boundaries. The architectural schema also passed Draft 2020-12 meta-validation using `jsonschema`. It is a lightweight check, not a comprehensive secret scanner or JSON Schema validator. The publication review additionally inspected tracked content and excluded private runtime data, source PDFs, private chats, source-app screenshots and account details.

## Explicit limits

- No paid provider calls, subscriber login flows or live model sessions were exercised.
- ACP is a fixture-tested transport core, not verified full vendor-extension compatibility.
- HTTP adapters are non-streaming, text-only subsets; no tool loop or automatic fallback.
- The reference planner is deterministic, and acceptance creates local records only.
- No background scheduler, distributed worker lease, hosted deployment or multi-user access is implemented.
- Browser preference persistence is not cross-device layout synchronization.
- Source applications' historical test counts and live-state claims were not reused as foundation evidence.
- GitHub Actions defines Linux Python 3.11/3.14 and browser checks; its live result should be read from GitHub, not inferred from this local record.
