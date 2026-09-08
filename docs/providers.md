# Subscriptions, ACP and model endpoints

**Research checked 2026-09-08.** This is a public instruction/template repository for users to construct and operate their own private, locally scoped AgentOS. The primary agent lane uses each user’s own native account session; it is not a shared credential gateway or hosted inference service. Technical compatibility, authentication, entitlement, and permission to distribute an integration are separate questions. This table records documentation/source evidence, not a live test of the reader’s accounts. All integrations remain opt-in. See [provider setup](provider-setup.md) for the implemented local job path.

## Two integration lanes

1. **Agent lane:** your AgentOS talks to an existing coding-agent runtime through ACP or its native protocol. The runtime owns its agent loop, supported login, model catalog and capabilities. An eligible subscription may pay for this work.
2. **Model lane:** your AgentOS owns the loop and calls an explicitly configured OpenAI- or Anthropic-style endpoint with an authorized API credential. Endpoint compatibility does not establish subscription billing.

ACP here means **Agent Client Protocol**: a client-to-agent protocol. It is not MCP, an OpenAI-compatible inference API, or permission to repurpose subscription tokens.

## Compatibility matrix

| Product/runtime | Transport path | Existing subscription route | Limits and decision |
| --- | --- | --- | --- |
| ChatGPT through **Codex** | Native Codex App Server, or `@agentclientprotocol/codex-acp` bridging it to ACP | Codex’s supported ChatGPT sign-in where the account has access | Keep native credential ownership; API-key sign-in uses API billing. Do not treat ChatGPT web itself as an ACP server. [Auth](https://learn.chatgpt.com/docs/auth), [adapter](https://github.com/agentclientprotocol/codex-acp) |
| **Claude Code / Agent SDK** | ACP adapter `@agentclientprotocol/claude-agent-acp`, or native SDK integration | User installs and signs into unmodified Claude Code using their own eligible subscription; the local workspace retains that native session boundary | Native user-owned Claude Code subscription use is explicitly distinguished from third-party credential intermediation. Verify the selected ACP adapter’s native runtime/auth path; direct model calls use API credentials. [Adapter](https://github.com/zed-industries/claude-agent-acp), [SDK rule](https://code.claude.com/docs/en/agent-sdk/overview), [authentication policy](https://code.claude.com/docs/en/legal-and-compliance) |
| **Grok Build** | Native `grok agent stdio` ACP | Supported local Grok login; current subscription documentation includes Build in its usage model | Eligibility and quota require account-level confirmation. ACP also accepts supported API-key auth; do not silently switch billing routes. [Build](https://docs.x.ai/build/overview), [ACP](https://docs.x.ai/build/cli/headless-scripting), [usage](https://docs.x.ai/grok/faq) |
| **Cursor CLI** | Native `agent acp`; installations may expose the executable as `cursor-agent` | Supported Cursor account browser login; availability and usage follow the account | Resolve the exact executable, avoid the generic `agent` name collision, and verify the account’s model catalog. Cursor API keys are not OpenAI model API keys. [ACP/auth](https://cursor.com/docs/cli/acp), [CLI auth](https://docs.cursor.com/en/cli/reference/authentication) |
| **Hermes Agent** | Native `hermes acp` server with its configured model backend | Depends on the selected backend and its provider’s permissions | Hermes is an agent runtime, not a blanket entitlement to every subscription. Reuse its architecture; do not infer provider permission from Hermes implementation alone. [ACP](https://hermes-agent.nousresearch.com/docs/user-guide/features/acp), [providers](https://hermes-agent.nousresearch.com/docs/integrations/providers) |

The four requested commercial subscriptions are covered. Other ACP agents can be added through the same negotiated client path; the [ACP agent directory](https://agentclientprotocol.com/get-started/agents) is discovery evidence, not an account-access guarantee.

## Important research findings

**Codex adapter migration:** the older `zed-industries/codex-acp` README directs new work to `agentclientprotocol/codex-acp`. The maintained adapter starts Codex App Server and maps operations/events. Do not implement against stale package instructions just because an older client worked. [Migration notice](https://github.com/zed-industries/codex-acp)

**Claude: preserve the native user-owned boundary.** Anthropic’s current policy explicitly permits users to sign into the unmodified Claude Code binary with their own subscriptions. It prohibits developers collecting, storing or intermediating Claude.ai session credentials or routing them on behalf of users. This foundation’s intended path is user-installed Claude Code, Anthropic-owned sign-in, private workspace/session scope, and a local client around that native runtime. Publicly sharing these instructions does not make this a hosted login or inference service. For an ACP adapter, verify its actual native runtime/authentication behavior; do not replace it with a token-extracting API proxy. [Current policy](https://code.claude.com/docs/en/legal-and-compliance), [native authentication](https://code.claude.com/docs/en/authentication)

The SDK overview gives a shorter third-party-product restriction; the fuller policy distinguishes native Claude Code use. Do not flatten these into a blanket “Claude subscriptions cannot work” claim. Likewise, do not treat local execution alone as permission for any arbitrary credential mechanism. Personal Claude, Codex and Grok sessions fit the same AgentOS instance model, even though their transports differ.

**Hermes provider claims:** the inspected Hermes provider documentation describes several subscription/OAuth routes and provider-specific restrictions. Those are Hermes’s implementation claims; they do not supersede provider policy. The same docs distinguish custom `chat_completions` and `anthropic_messages` transports, a useful architectural pattern. The foundation does not borrow another app’s token files or implement token impersonation. [Hermes provider guide](https://hermes-agent.nousresearch.com/docs/integrations/providers)

**Session persistence drifts:** current Hermes `acp_adapter/session.py` says sessions persist through its SessionDB, and `server.py` advertises load/list/resume/fork. Older search results described process-local session persistence. Use pinned source plus an actual restart test for the installed version. See the immutable links in [provider patterns](provider-patterns.md).

## Configuration model

A driver describes a protocol implementation. An instance describes one account, credential owner, runtime environment, base URL and policy. A session belongs to one instance and workspace. Never share mutable session state merely because two instances use the same model brand.

Record `driver`, `instance_id`, `transport`, `auth_kind`, `billing_route`, `model_id`, `capabilities`, `version`, `policy_revision`, `verification_state`, and `last_verified_at`. Keep secrets as environment-variable or credential-store references. `unknown` is a useful billing state; zero dollars is a claim.

Do not fallback from subscription to paid API, change provider, or switch model silently. A fallback needs explicit configuration including data egress, budget and allowed task type. Account login and model access are separate readiness checks. Quota failure does not justify rotating accounts to evade limits.

## ACP integration sequence

Resolve a pinned executable and approved isolated runtime configuration. Start the process with an argument vector. Exchange `initialize`, verify protocol version and capabilities, then perform only the supported authorized authentication flow. Create or load a session, send prompts, normalize updates, and handle permission/questions. Preserve native option IDs. `session/cancel` is a notification; it does not itself prove termination. [Protocol flow](https://agentclientprotocol.com/protocol/v1/overview)

Absent capabilities are unsupported. Discover models and modes rather than hardcoding a marketing name. Advertise only client features actually implemented. In particular, disabling client filesystem/terminal capabilities does **not** sandbox an agent’s own tools or prevent startup hooks. Project-only scope must be enforced by native configuration and process confinement, not by an empty `mcpServers` list. [Negotiation](https://agentclientprotocol.com/protocol/v1/initialization)

## Endpoint support

`adapters/http_models.py` implements explicit text-only request/response paths:

| Dialect | Base URL convention | Request path | Authentication | Scope implemented |
| --- | --- | --- | --- | --- |
| `openai-chat` | Include provider prefix, usually `/v1` | `/chat/completions` | Bearer key from named env var | Text messages and bounded completion |
| `openai-responses` | Include provider prefix, usually `/v1` | `/responses` | Bearer key from named env var | Text input/instructions and output text |
| `anthropic-messages` | Include provider prefix, usually `/v1` | `/messages` | `x-api-key` plus version header | Text messages, top-level system and max tokens |

See [OpenAI Chat](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create), [Responses](https://developers.openai.com/api/docs/guides/responses), and [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create). A compatible endpoint may implement only a subset. The Chat adapter uses `max_completion_tokens`; providers that accept only a legacy token field need an explicit dialect extension and tests.

The HTTP module intentionally does not implement a tool loop, SSE, images, reasoning-option translation, retries or automatic fallback. It rejects truncated/tool-required output instead of calling it complete. Expand capabilities one at a time with contract fixtures and a permitted live smoke test. The ACP module receives streaming updates but remains a small transport core, not a complete provider-specific client.

## Verification ladder

1. Static inventory: executable, pinned version, transport and capability configuration.
2. Initialization-only probe: no auth browser, session startup or model calls as a health-check side effect.
3. Explicit login through the supported provider flow; keep token exchange owned by that provider.
4. One harmless permitted prompt in a disposable confined workspace; record model, transport, result and billing route when observable.
5. Test interruption, approval denial, unsupported extension, expired auth, reconnect and restart. Verify no inherited global integrations.
6. Connect the production composer only after those boundaries pass. Until then label the instance configured or unverified.

This repository verifies the transport modules against controlled peers. It does not claim successful live subscription sessions for any provider.
