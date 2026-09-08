# Build your own AgentOS

1. Read `docs/arms.md` to understand what each layer owns and how they interact.
2. Fill `templates/product-brief.md` with the user’s real recurring job. Select only one first workflow. Use `examples/` for shapes, never as invented user facts.
3. Inspect tools and authorizations. Fill `templates/capability-matrix.md`; configured is not verified. Keep unknown access explicit.
4. Choose three to six domain objects and their relationships. Complete `templates/domain-model.md` and `templates/work-order.md`.
5. Read `docs/design/spatial.md` and make three compositions before selecting one. Complete `templates/design-brief.md`. A map is optional; a useful spatial hierarchy is required.
6. Run the reference once to understand persistence and review. Choose the target stack deliberately. The reference is a teaching implementation, not a framework mandate.
7. Use the `agentos-builder` project skill. Build the first vertical workflow and test its failure states. Add memory routing, then bounded scheduling, then integrations justified by the workflow.
8. Complete `docs/acceptance.md` and record evidence in `templates/handoff.md`. A public repository is not an internet-accessible application and does not activate execution.

## Reading budget

First session: AGENTS, this file, the ARMS model, and product brief. Design session: the spatial skill plus its referenced design documents. Runner session: architecture, operations, and routine template. Do not stuff all skills or the whole source archive into every prompt.

## Choices to resolve

Purpose and owner; authoritative inputs; desired artifact; permitted writes; local or shared access; stable object identity; how the user reviews and stops work; source freshness; preferred composition; accessibility needs. Infer low-impact implementation details from the workspace. Ask for the few decisions that change authority or the product.

## Start from a working loop

For research: source → evidence note → review → research brief.
For operations: intake → plan → review → project and tasks.
For portfolio-style monitoring: dated snapshot → analysis → review → recorded decision. Financial execution is a separate extension, not bundled here.

Track readiness per capability as `specified`, `implemented`, `tested-with-fixtures`, or `verified-live`. Keep a next action for everything unfinished.
