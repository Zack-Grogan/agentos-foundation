# Build your own AgentOS

Read `AGENTS.md`, then `START-HERE.md`. This repository is a public instruction/template foundation for a user's own private local workspace. Use the relevant project playbooks in `.agents/skills/` by reading their `SKILL.md` directly; do not assume they were installed into a client-specific native skill registry.

For personal subscription use, keep authentication in the unmodified native Claude Code runtime and Anthropic's own login flow. Do not collect or proxy subscription tokens. See `docs/providers.md` for researched distinctions across Claude, Codex, Grok and Cursor, and for separate API endpoint support.

Read `docs/design/spatial.md` before building the workspace and `.agents/skills/composer-design/SKILL.md` before building its composer. Inspect the actual domain and capabilities, then complete one source-to-reviewed-result workflow. Keep private runtime data out of this public repository.
