# Architectural interchange contracts

`agentos.schema.json` contains nine named JSON Schema definitions. Validate a specific record against its named `$defs` definition, or use the top-level union. These contracts guide a custom implementation; the smaller local reference record format is documented in its source.

Structural schemas cannot enforce semantic constraints such as unique widget IDs, ownership, source existence, freshness, digest equality, revision conflicts or permitted transitions. Enforce those in domain services and behavioral tests. A schema’s `format` is annotation unless the chosen validator enables format assertion.

Provider instance, session and model identity are distinct. Never put credential values in these records. Use private server-side secret references. Negotiate ACP capabilities at runtime rather than filling this schema with assumed support.
