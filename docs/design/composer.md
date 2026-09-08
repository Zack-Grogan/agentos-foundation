# AgentOS composer design

Use this with the `composer-design` project skill. Patterns are grounded in the pinned AI Elements and T3 Code sources in `docs/provider-patterns.md`; the following layout and acceptance rules are this foundation’s design recommendations.

## Anatomy

```text
┌─ Context rail: selected object · source revision · attached files ─┐
│                                                                 │
│  Write the next instruction…                                     │
│  Grow to a bounded height, then scroll internally.                │
│                                                                 │
├─ + Attach  / Procedure    Account · Model · Mode       Send ↵ ────┤
└─ Actual connection / upload / limit feedback when relevant ──────┘
```

The context rail is visible before sending. It shows what will be sent, with removal and source inspection. Keep the writing surface dominant. Put low-frequency options in a compact menu; keep account/model identity visible when switching changes capability or billing. The same structure fits a corner drawer, workbench panel or dedicated conversation app.

On narrow screens, let context chips wrap or scroll with obvious overflow, stack feedback, and collapse options into a menu. Keep Send reachable above the software keyboard. Use a separate explicit send gesture on mobile so normal typing does not accidentally dispatch.

## State model

Maintain independent draft, upload, connection, turn and permission state. Derive controls from their combination instead of one overloaded loading boolean.

| State | Primary control | Preserve |
| --- | --- | --- |
| Draft ready | Send | Text, context, provider selection |
| Attachment uploading/failed | Disabled Send with reason; retry/remove | Draft and per-file state |
| Connecting | Connection feedback | Draft until server accepts request |
| Turn running | Stop; optional queue only if implemented | Partial response and next draft |
| Stop requested | Stopping feedback | Request/run identity; no false stopped claim |
| Needs permission or answer | Explicit scoped decision controls | Native request and option IDs |
| Disconnected | Reconnect/check state | Partial output and logical request identity |
| Failed | Specific recovery action | Failed input and evidence |

A new message, a reply to a pending question, and an approval are different actions. Do not route them all through “send prompt.” A provider that cannot steer a live turn must not show a working “Send now” control.

## Input behavior

Enter sends only under the chosen desktop convention; Shift+Enter inserts a newline. IME composition must never trigger submission. Respect browser composition events and avoid clobbering caret selection during a render. Validate the serialized provider input, including expanded citations and attachment references, before dispatch.

Use one server-recognized request ID per logical submit. Retain it on uncertain delivery. Clear only the submitted draft after server acceptance; do not erase text typed while the request was being sent. If draft editing continues during upload, attach the right revision at dispatch.

## Attachments and context

Validate type/size/count on the server as well as in the UI. Show upload progress only when measured. Revoke temporary preview URLs. Persist metadata with environment identity and retention policy; after restart, expired/missing files need reattachment, not a misleading ready badge. A visible file path is not permission to read it.

Context from a domain object uses its ID, revision and source reference. Save a readable quoted excerpt so a changed/deleted source remains understandable; mark it stale and offer the current source. Never silently broaden selected context to the entire workspace.

## Provider controls

Show an instance/account label, protocol lane and model chosen from the actual catalog. Hide unsupported image, effort, mode or tool controls. Show subscription, API, or unknown billing route honestly. Changing providers does not transfer session state automatically; create a new session with an explicit handoff packet when migration is needed.

## Visual craft

Use a single framed writing surface with quiet borders, clear focus, readable placeholder and balanced internal spacing. Context chips are references, not status confetti. Keep source, error and permission accents distinct. A large hero-style prompt box wastes attention in an operational workspace. The conversation can grow while the main domain work remains usable.

## Acceptance fixtures

1. Empty draft, multiline draft, long serialized citation, unsupported model option.
2. IME Enter, Shift+Enter, selection replacement, mobile keyboard.
3. Upload failure, duplicate file, expired attachment after reload.
4. Drawer close/reopen; thread and provider switch; unsent draft recovery.
5. Duplicate submit; lost response; typing during submit; no double dispatch.
6. Silent provider; Stop requested then confirmed; interrupted partial output retained.
7. Blocking permission and asynchronous question; native option IDs returned correctly.
8. User scrolls up while text streams; source opens and returns to the same place.

The reference workspace uses a real capture form and a documentation drawer. It does not pretend to be a complete streaming composer; use these fixtures when implementing a connected assistant.
