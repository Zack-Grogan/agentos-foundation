# From repeated work to a custom system

## 0. Discover the actual job

Observe one recent task. Name its inputs, the decision being made, its output, its current manual steps, and the person accountable. Inspect existing code and tools before choosing a replacement stack. Record missing access and existing constraints. Deliver `product-brief.md` and `capability-matrix.md`.

**Gate:** describe success without naming a model or visual theme.

## 1. Establish identity and authority

Define the domain’s objects and stable IDs. Map which service may change each record. Separate drafts, accepted decisions, and external effects. Choose private runtime storage and a public code/config boundary. Deliver the domain model and one work order.

**Gate:** an agent cannot bypass the same validation the UI uses.

## 2. Make one skill useful

Write a short project skill with selected input, output schema, source rules, stop conditions and a missing-input path. Run it manually. Preserve its output as a reviewable artifact. Start deterministic where possible; insert model inference only where it adds useful judgment.

**Gate:** one normal and one incomplete input produce honest outcomes. A tool refusal does not become a fabricated success.

## 3. Give context a durable home

Add source records, relative-path routers, dated decisions, and a handoff. Store source revisions or hashes. Distinguish extracted facts, inferred suggestions and accepted decisions. Define expiry/revalidation and deletion propagation into derived indexes.

**Gate:** three fresh-session questions resolve to expected evidence, including a changed or missing source.

## 4. Design the workspace as an instrument

Draw the domain relationships and choose board, map, timeline, desk or hybrid. Compare three compositions against the same task. Begin with three useful instruments: review, recent work, domain focus. Introduce no metric without a definition and provenance.

Build a representative normal, empty, stale, blocked and failed state before expanding the chrome. Make inspectors retain location, focus and scroll. Chat stays recoverable and secondary. See `docs/design/`.

**Gate:** a user can find a source, review a result and identify a failure with chat closed.

## 5. Make the workflow durable

Persist run identity before work; attach the input and skill revisions. Add cancellation, deadlines, idempotency, and explicit interrupted/unknown states. Keep transactions short around external calls. Write output and validation evidence before reporting success.

**Gate:** duplicate launch, crash, lost response and malformed output do not duplicate work or hide uncertainty.

## 6. Add the routine

Prove the manual flow before scheduling it. Select execution location based on input access. Define timezone, DST, missed-run behavior, overlap policy, retry budget, owner and pause control. Local work remains local unless an always-on requirement justifies moving it.

**Gate:** observe a scheduled result at the intended destination. For laptop-off claims, actually test with the laptop off; a fixture or manual trigger is insufficient.

## 7. Add the application connection

Prefer an official maintained CLI for operations, or a narrow API/MCP when appropriate. Specify the exact operation, scopes, credential owner and revocation. Test a permitted read; test writes only within their authorization. Never offer arbitrary shell execution from a browser.

**Gate:** the real data path and its failure mode are verified independently from installation.

## 8. Operate and evolve

Document start, stop, restore, migration and failure ownership. Validate restoration, not merely backup creation. Measure useful artifact acceptance, source coverage, time to review and failures when the underlying measurements exist. Revisit skills and layouts from observed use.

**Gate:** someone else can operate the system from the repo without reconstructing private chats.

## Adoption cadence

A seven-session sequence can be skill, skill references, memory, routine, app, command centre, failure/handoff review. It is a learning cadence, not a delivery estimate. Stop at the last useful working level.
