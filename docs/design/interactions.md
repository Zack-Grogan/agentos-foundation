# Interaction contracts

## Object inspector

Open by stable object ID. Preserve selection, filters, tab and scroll. Use a real modal only if the background is unavailable; otherwise implement a non-modal panel without claiming modal semantics. A modal needs an accessible title, focus inside it, a contained tab sequence, a close control and focus restoration. Escape closes the top applicable surface. [W3C dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

Closing a window does not necessarily cancel work. During an uncertain mutation, preserve the request ID and offer status lookup. If refresh fails, retain readable data with a stale/error message. A missing source has an explicit unavailable state.

## Arrangement

Save widget IDs, order, visibility, size and layout version. Give drag operations clickable alternatives such as Move earlier/later and size presets; keyboard-only equivalence alone is insufficient for users who cannot drag. [W3C dragging guidance](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)

Provide restore-hidden and reset-layout controls. Validate minimum size and ensure controls remain reachable. For shared or multi-window persistence, use layout revisions and resolve conflicts. Prototype browser-local storage is a convenience, not shared durable state.

## Composer

Keep draft text across accidental dismissal. Show attached context explicitly. Distinguish sending, queued, streaming, stop-requested, stopped, interrupted and failed. Stop must reach the backend/provider before claiming the run stopped. Retain partial output. Dedupe a submission by request ID, not button-disable timing.

Autoscroll only when the user is following the newest message. Otherwise offer a new-messages indicator. Surface sources and tool results as inspectable evidence. Do not expose hidden chain-of-thought; show concise progress, actions and results. History and retries need stable identities.

AI Elements and T3 Code are useful interaction references, not requirements to migrate every app to React. Their source licenses and current APIs must be checked before reuse. The reference here does not include a fake assistant conversation or pretend to call a model.

## Voice

Voice is an optional adapter. Require an explicit Start gesture; show connection, listening, speaking, muted and ended states. End closes capture, audio playback, network session and server resources. Use short-lived credentials when the provider supports them. Apply the same capability policy as text, with a deliberately narrow initial tool set. A handshake test is not audible microphone/playback proof.

## Review and action

Present the artifact revision, source window, proposed change and validation. Acceptance refers to that exact content. Disable or reject stale acceptance. An accepted draft is still not an external send unless the approved operation includes it. Rejection preserves the draft and reason. A retry cannot create duplicate accepted objects.

## Truth-state matrix

| State | Display | Action |
| --- | --- | --- |
| Empty | No records yet; describe first useful input | Capture or connect |
| Partial | Known content plus named omissions | Inspect coverage |
| Stale | Last observed date and stale label | Refresh permitted source |
| Blocked | Missing capability or dependency | Resolve prerequisite |
| Running | Actual run identity and start time | Inspect or request stop |
| Failed | Error and affected result | Diagnose / bounded retry |
| Unknown | Effect not confirmed | Reconcile, not blind repeat |
| Needs review | Artifact and validation | Inspect and decide |

Test every state with fixtures before calling the component complete. Label fixtures at the workspace level and on exported evidence.
