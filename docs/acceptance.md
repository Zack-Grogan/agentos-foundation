# Acceptance gates

Keep evidence for each gate: command/action, environment, timestamp, actual output, and limitations. See `docs/verification.md` for this template’s current checks. These production extension requirements are not claims that the reference implements them all.

| Area | Required behavior |
| --- | --- |
| Input | Normal, missing, oversized and malicious text handled; original evidence preserved |
| Skill | Same contract in manual and launched execution; missing references stop usefully |
| Memory | Three retrieval questions; changed/deleted source invalidates derived claim; exclusions stay excluded |
| Run | Unique request ID, duplicate suppression, bounded execution, output validation, crash/interruption behavior |
| Review | Exact revision/digest; stale and forged review rejected; repeated acceptance creates one result |
| Routine | Timezone/DST, missed runs, overlap, pause, restart and output delivery tested |
| External effect | Current scope/freshness rechecked; intent persisted before call; lost response reconciled |
| Concurrency | Competing claims tested on deployment DB; stale worker cannot finalize |
| Integration | Real allowed read, revoked auth, unavailable provider, safe output handling |
| Interface | End-to-end work with chat closed, source open, return continuity, keyboard and click-only arrangement |
| Narrow layout | No horizontal overflow at 390px; long content; sheet and focus controls reachable |
| Security | No arbitrary shell/path endpoint; origin/session controls; escaped content; private data not served |
| Recovery | Backup restored into new location; source, artifact and accepted records compare correctly |
| Handoff | Exact start/stop, data location, scope, tests and unresolved boundaries recorded |

## Minimal live proof

Capture a permitted input, run the chosen skill, inspect its artifact and evidence, accept a specific revision, open the accepted record, restart and find it again. Then repeat the same request ID and confirm no duplicate. Induce a safe validation failure and confirm it cannot be accepted.

## Evidence levels

`specified` means a contract or plan exists. `implemented` means code exists. `tested-with-fixtures` means controlled inputs passed. `verified-live` means the actual integration and intended environment produced the result. Record these per capability. Never carry an old chat’s test counts forward as present verification.
