# Research worked example

Input: [input.md](input.md), a synthetic fixture. Shared shell: central circle and layered orbits. Contextual work view: **Evidence workbench**.

1. Scaffold this profile using `scripts/new_workspace.py`.
2. Import `examples/worked/research/input.md` using the CLI, or capture its text in the app.
3. Run capture-to-plan using the local provider. Expected: one succeeded job, one pending draft, source ID/digest attached by the server, and no accepted project yet.
4. Inspect the source and draft. Unknown accuracy, cost and latency remain unknown; source is inspectable beside the draft.
5. Accept the exact draft digest. Expected: one project with proposed tasks; repeat acceptance and confirm no duplicate.
6. Search Memory and find both source and accepted decision. Edit the source; expected: the earlier decision is marked stale.
7. Create a paused routine. Enable it explicitly and use CLI tick/work-once for a controlled occurrence. Repeating the tick creates no duplicate.

The deterministic provider returns a generic scaffold, not domain inference. To evaluate a configured model, preserve the same JSON output contract and assert the domain conditions above. Save the actual output and error evidence; never call the model-specific example verified from the local fixture alone.

## Design comparison

Map: helpful for stable relationships, weaker for reading a full document.
Board: helpful for stages of work, weaker for close source comparison.
Workbench: helpful for evidence and long artifacts, weaker for monitoring many independent entities.

The selected profile keeps the orbital center and demonstrates its contextual work view in an app window. Keep the app-shell rules: compact observation strip, no website footer, contextual app windows and a secondary assistant surface.
