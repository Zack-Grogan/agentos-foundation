# App shell: header, lower edge and widgets

These rules generalize the confirmed G-Portfolio spatial decisions. The source of truth is its project design brief and active spatial shell, rather than the older page template that still contains a conventional footer. The foundation reference now demonstrates the same app-first structure with synthetic research records.

## Header: an instrument strip, or nothing

- Do not add a brand masthead, welcome headline, slogan, breadcrumbs row and global menu merely because this is rendered in a browser.
- The top edge earns its space by showing information the user checks during work: domain observations, selected workspace, attention counts or connection freshness.
- Keep it compact: roughly 48–56px is a useful starting budget. It must not push the working surface below a large introduction.
- Label comparable values precisely. G-Portfolio separates unit price from owned position value. A generic OS must distinguish queued from running, drafted from accepted, or observed from target.
- Attach timestamps and partial/stale/unknown state to the actual observation. A recent page refresh is not a recent source observation.
- Open the matching object or filtered app from each interactive readout. Do not make every strip item link to the same generic page.
- Allow horizontal overflow inside the strip when necessary; never make the whole application horizontally scroll. Hide low-priority readouts on narrow screens without removing access to their detail.
- Product identity may be a small workspace mark or part of the domain center. It does not deserve a marketing header by default.

## Lower edge: controls, not a website footer

Do not render copyright rows, link columns, repeated branding, implementation descriptions or a full-width promotional/status footer in the workspace. Put About, attribution and technical information inside an app/settings surface. Keep attribution in the repository documentation.

The lower edge can carry three compact utility anchors:

| Anchor | Purpose | Rule |
| --- | --- | --- |
| Left | Actual runtime state and an applicable control | Pause/stop/arm only when the backend supports that exact operation; never imply an action from decoration |
| Center | All instruments / layout / settings | Restores hidden apps and reaches lower-frequency tools |
| Right | Assistant launcher | Small, always recoverable; opens an in-app drawer; never a permanent chat card |

These controls float at the workspace edge without moving the central composition. A narrow screen may use a small fixed control tray, with enough safe-area padding and content clearance. This is an interaction surface, not a site footer. State belongs near the affected control; do not stretch one generic “all systems live” badge across the bottom.

The reference has a Guide launcher in the future assistant position. It is clearly documentation, not a fake connected assistant. Its schedule indicator is off and it does not offer a pretend pause button.

## Widgets are app instruments

A widget is a compact lens into an application or domain object, not an isolated card invented to fill a grid. Its expanded inspector must reach the full useful workflow. Preserve existing domain services and permissions when changing presentation.

**Required contract:** stable widget ID; user question; canonical source; relevant object/filter; refresh mechanism; source freshness; truth states; summary fields; primary action; inspector target; minimum size; arrangement options; narrow-screen destination; focus/return behavior.

Design each instrument for its content:

- Balances or capacity: aligned readouts with clear units and coverage.
- Reviews or incidents: dated timeline and actionable state.
- Recent work: compact event rows linked to real runs.
- Research: an in-app reader, source metadata and genuinely distinct filters.
- A procedure: one useful launch path with its input and permission scope.

Avoid equal rounded cards, repeated giant headings, empty padding, decoration-only charts and a widget for every backend module. Start with three useful summaries and the domain work surface; add only what earns repeated use. A widget may be unboxed, divided by a fine rule, or layered only when that depth explains behavior.

## Arrangement and persistence

For an anchored-map composition, keep equal-width left and right instrument rails so the domain center stays at the viewport center. Opening an inspector or assistant overlays that canvas; it must not squeeze the rails and shift the center. Other compositions should define their own equally explicit invariant.

Make customization explicit through All instruments: add/show, hide, restore, reorder, and supported size/collapse controls. Preserve widget IDs and validate layout versions/revisions. Save presentation independently of application records. Never delete domain data when removing a widget. Dragging is optional; clickable controls must perform the same supported arrangement actions. Do not implement a fake resize handle.

The small reference implements show/hide/restore for selected instruments, rail swapping, and a list/map view. It does not claim a complete freeform drag/resize manager. Custom applications can add those capabilities using the widget contract and interaction tests.

## App windows and continuity

A click opens a contextual inspector or app window over the workspace. Preserve selected object, active tab, filters and scroll on return. Use domain-specific tabs (for example related news within an asset), not a second global site navigation. A source link remains available, but a reader should not eject the user from their current task unnecessarily.

Large forms and occasional setup flows belong in an app window. The reference’s full capture form opens from New capture, freeing the instrument rail for actual working context.

## Rejection criteria

Reject a proposed design if it introduces a large welcome/hero title, a conventional footer, a sidebar of one-widget pages, an equal-card dashboard as the default, a permanent chat panel, a moving center, or controls without real behavior. A design is not fixed by changing its colors while keeping those website structures.

## Verification

At desktop width, measure the center before/after opening an inspector and arrangement controls; it should not move. Assert there is no conventional footer and the top strip stays within its budget. Complete capture/review/source navigation without leaving the workspace. Test hide/restore without data loss and keyboard/click-only operation. At narrow width, use a deliberate ordered composition and keep the control tray from covering content.
