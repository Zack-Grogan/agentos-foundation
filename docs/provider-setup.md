# Configure a user-owned provider

The default `local` instance always works without credentials. Opt-in configured endpoints and ACP sessions use the same durable source/job/artifact/review path. This is a text-plan integration, not a general-purpose coding-agent console or full streaming conversation UI.

## API endpoint

1. Initialize the workspace with `python3 -m reference.cli init`.
2. Copy `templates/runtime-providers.json` to `.agentos/providers.json` if no provider file exists. Preserve existing instances when adding one.
3. For `my-api`, select `openai-chat`, `openai-responses` or `anthropic-messages`, set the verified base URL and model ID, and name the environment variable holding the API credential. Never put its value in the file.
4. Supply that environment variable to the server/CLI through your normal secure setup. The child receives only the configured credential reference, not every credential in your shell.
5. Set `enabled` to true, run `doctor`, then explicitly select this instance for a harmless source and Run skill.

The model must return the plan JSON described in `reference/validation.py`. Invalid, truncated or unsupported tool output fails without acceptance. Requests use explicit output limits, no redirect-following, no implicit proxies and no retries or billing fallback. The supervising worker additionally enforces total wall-clock time and a 2MB aggregate output limit.

## Native subscription through ACP

Install and authenticate your selected native runtime using its current official instructions. [The compatibility guide](providers.md) identifies the native or adapter path for Claude, Codex, Grok, Cursor and Hermes.

Configure the `my-agent` instance with an absolute executable argument vector. Examples of argument shapes are an installed Claude/Codex ACP adapter executable, Grok's executable plus `agent`, `stdio`, Cursor's executable plus `acp`, or Hermes plus `acp`. Pin the adapter/runtime version you validate. A marketing model name is not a command or a negotiated model ID.

`env_refs` maps each environment variable the native runtime should receive to the name of an explicitly supplied environment variable. Values in this JSON are variable **names**, never credentials. Native configuration/profile locations are supplied through the runtime's documented mechanisms. Keep sign-in in the native application's supported flow; do not extract tokens into this template.

Before enabling, review the native runtime's filesystem sandbox, inherited instructions, MCP servers, skills, hooks and tool permissions. Set `scope_reviewed` and `auth_owned_by_user` only after doing so. The runner supplies a per-instance private working directory. Empty ACP client capabilities and `mcpServers: []` do not disable an agent's own built-in tools or startup configuration.

The built-in client denies incoming permission requests and does not expose client file/terminal operations. This is suitable for a bounded text-plan workflow once native scope is configured. Workflows needing tool grants, provider-specific questions or plan approvals require an explicit extension; they are not silently auto-approved. Authentication-required sessions fail usefully rather than launching a login as a background side effect.

## Diagnostic states

- `ready-local`: deterministic planner ready.
- `disabled`: configuration present but not enabled.
- `credential-missing` / `setup-required`: named environment variable or executable missing.
- `configured-unverified`: static prerequisites present; no live claim.

Doctor never reads credential values into its output, logs into an account, creates a session or spends usage. A malformed provider file leaves local browsing and local work available; external jobs fail until corrected. A changed provider configuration invalidates queued/running jobs before result adoption.

## First verified run

Use one non-sensitive source. Run the selected provider, inspect its job receipt and source-linked draft, then test Stop and an invalid-output case with a controlled peer. Confirm the actual account and billing route in the native provider before relying on schedules. A successful fixture does not verify the reader's subscription entitlement.

On macOS/Linux the worker terminates its process group and the ACP adapter performs native subprocess cleanup. Windows process-tree confinement remains a platform-specific extension; do not claim identical containment from direct process termination.
