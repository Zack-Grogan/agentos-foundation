# Visual grammar

## Roles before colors

Define background, instrument surface, raised inspector, primary text, secondary text, border, focus, selection, action, success, warning and failure tokens. Keep selection distinct from permission and success. Status always includes readable text. Theme tokens should not encode domain policy.

Suggested starting palette: warm charcoal field, ivory text, muted stone secondary text, amber focus and action, desaturated sage success, coral failure. This is one example, not an AgentOS brand requirement. Research might use a light editorial workbench; field operations might need outdoor contrast. Record the actual audience and lighting conditions.

## Type

Use a readable system sans for controls and data. An optional serif can give domain headings or an artifact editorial character. Tabular numbers help comparisons. Keep body text near 16px; reserve smaller text for secondary metadata and verify readability in the rendered design. Clear labels beat symbolic icons that need decoding. Do not reduce every label to a faint uppercase micro-caption.

## Rhythm

Use a small spacing scale such as 4, 8, 12, 16, 24 and 32. Different instruments may have different density while aligning on a shared grid. Let the domain focus breathe; compress repeated chrome. A large card with one number is usually wasted space unless that number is the user’s principal decision.

## Depth and material

Use subtle borders and a small set of elevation roles. The field, instrument and inspector should be distinguishable without neon glow. A graph line communicates a relationship, not a decorative background. Do not use animated particles, fake terminals or decorative telemetry to imply intelligence.

## Motion specification

Start with 120–220ms transitions for local state changes and 180–280ms for entering an inspector, then test perception. Avoid delayed controls. Respect `prefers-reduced-motion`. Work in progress is driven by real events; indeterminate indicators must say what is waiting. A timer is elapsed time, not percent complete.

## Design tokens in code

The reference uses CSS custom properties in `reference/web/style.css`. Copy roles, not its palette, into a custom product. Add density/theme variants only when they serve observed needs. Validate focus, hover, selected, disabled and error states in both themes before offering a toggle.

## Design quality checklist

Primary task visible on entry; center or artifact dominance clear; supporting instruments unequal when their jobs differ; dates legible; actions specific; no placeholder business metrics; no silent stale state; detail preserved on return; chat recoverable; narrow screens useful; motion purposeful.
