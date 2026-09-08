# Designing an AgentOS workspace

Apply [the app shell rules](app-shell.md) first. A compact data strip, lower-edge utilities and contextual instruments replace website header/hero/footer structures.

A good AgentOS makes work feel located. The user knows where to look, what changed, what it means, and what can be done next. Visual quality comes from the relationship between domain objects, spatial structure and interaction—not from adding a generic dashboard theme.

## Start with a work map

List three to six domain nouns: projects, experiments, clients, cases, positions or documents. Describe their actual relationships. Then list the recurring gestures: inspect, compare, annotate, propose, review, pause and return. Place information by those gestures rather than by backend table names or the ARMS acronym.

ARMS should power the system; it need not become four permanent navigation pages. A project inspector can reveal its sources (Memory), available procedure (Skills), recent jobs (Routines), and connected tools (Applications) in context.

## Keep the orbital shell; choose useful work views

| Composition | Fits | Spatial rule | Avoid when |
| --- | --- | --- | --- |
| Anchored map + instruments | A small stable set with meaningful relationships | Domain focus occupies the center; supporting rails balance it; inspectors overlay | Many unrelated objects create an unreadable graph |
| Workbench | Reviewing and arranging artifacts | Primary artifact gets most space; source and comparison tools sit beside it | No persistent artifact exists |
| Modular board | Several recurring independent jobs | Different widget sizes reflect frequency and depth; layout persists | Everything becomes an equal card |
| Timeline | Incidents, schedules, investigations | Time and causality drive placement; details remain in context | Dates are incidental |
| Hybrid | A stable domain center plus a review queue | One dominant composition; others become local lenses | It needs three simultaneous navigation models |

The template default is a central circle with multiple meaningful orbits. Keep it across profiles: inner orbit for domain work, outer orbit for ARMS capabilities. Compare three arrangements of orbital content and instruments, then choose the clearest one in `design-brief.md`. Workbench, board and timeline views belong inside contextual app windows; replacing the shared orbital center requires an explicit owner decision.

## The five layers of a workspace

1. **Field:** stable background and spatial frame. Quiet enough for sustained reading.
2. **Domain focus:** the primary map, artifact or work surface. Most of the attention budget belongs here.
3. **Instruments:** compact summaries that answer recurring questions. Each has a source, a state and one meaningful action.
4. **Inspector:** an object’s detailed view with provenance, history and available actions. Opening it preserves the workspace’s position.
5. **Assistant:** a recoverable corner control and supporting conversation surface. It knows explicitly selected context, not everything visible by assumption.

Critical review work remains reachable with the assistant closed. A connection’s green light is not a substitute for the last observed source time.

## Make a widget earn its space

For every widget write: user question; authoritative source; update mechanism; freshness; normal/empty/partial/stale/blocked/error states; primary action; detail target; minimum size; keyboard equivalent; narrow-screen destination. If those fields are empty, it is decoration or an unfinished idea.

Use at most three initial instruments. Add more because actual use warrants them. Remove redundant chrome before shrinking text. Treat a status strip as useful data, not a large brand masthead.

## Stable location and meaningful movement

Choose one coordinate system for the main composition. In an anchored map, opening a drawer must not push the center aside. In a workbench, resize only when the user deliberately changes comparison layout. Keep object placement stable across refreshes. Never reshuffle a graph randomly on every load.

Animate the selected relationship or the path from summary to inspector with bounded transform/opacity transitions. Use movement to explain cause and destination. Stop idle activity; do not invent agent activity with pulsing nodes. Provide reduced motion.

## Progressive depth

Glance: title, real state, one salient fact. Inspect: sources, relationships, provenance and available actions. Work: full editing or comparison surface. Return: same selection, filter and scroll position. Deep links identify the same object; opening a source must not lose the user’s task.

For more objects than the composition can display, provide search and a semantic list. Prefer focused neighborhoods over a giant force-directed hairball. A map’s adjacency is not statistical similarity unless actually calculated and explained.

## Narrow screens are a new composition

Below the working width, use an ordered list with the same object IDs and inspector. Put urgent review and domain focus first; stack instruments; open details as a sheet. Preserve desktop layout separately so a phone visit does not overwrite it. Never shrink the desktop canvas into illegible miniature controls.

## Deliverables before polish

A domain map, three composition sketches, a chosen rationale, one widget contract, all truth states, an inspector interaction, mobile translation, and a rendered workflow. Then use the design skills to tune typography, rhythm, color and motion. Ordinary web-design techniques remain useful inside this operating-system interaction model.
