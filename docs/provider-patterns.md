# Provider and composer source patterns

Source reviewed at these Git tree revisions on 2026-09-08. These are pattern extractions, not vendored implementations or guarantees about installed releases.

## T3 Code

Revision `47eed9face4186635488fba5f2494eddd13f6491`.

- [Provider constraints](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/docs/internals/providers.md): normalize protocol/account/capability differences at the adapter boundary; route sessions by provider instance; keep health checks free of login/setup side effects.
- [Codex driver](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/server/src/provider/Drivers/CodexDriver.ts): Codex instances own separate App Server/account lifecycles. T3 is not “ACP for everything.”
- [Shared ACP session runtime](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/server/src/provider/acp/AcpSessionRuntime.ts), [Cursor support](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/server/src/provider/acp/CursorAcpSupport.ts), [Grok support](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/server/src/provider/acp/GrokAcpSupport.ts): share lifecycle plumbing while preserving vendor authentication, model and extension differences.
- [Submission logic](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/web/src/components/chat/composerSubmission.ts): validate actual expanded provider input before dispatch and distinguish user-input replies from new turns.
- [Primary actions](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/web/src/components/chat/ComposerPrimaryActions.tsx): state-driven controls account for pending questions, provider availability, running turns and send eligibility.
- [Draft store](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/apps/web/src/composerDraftStore.ts) and [composer guide](https://github.com/pingdotgg/t3code/blob/47eed9face4186635488fba5f2494eddd13f6491/docs/user/composer.md): a draft carries more than text; attachments, citations and environment identity require explicit lifecycle and restore behavior.

## Hermes Agent

Revision `c8aa5608c24e3636e77c267650c0f1f52e44adb0`.

- [ACP server](https://github.com/NousResearch/hermes-agent/blob/c8aa5608c24e3636e77c267650c0f1f52e44adb0/acp_adapter/server.py): an existing agent can expose ACP while retaining its internal skills, tools and memory. Protocol initialization advertises supported session operations.
- [Session manager](https://github.com/NousResearch/hermes-agent/blob/c8aa5608c24e3636e77c267650c0f1f52e44adb0/acp_adapter/session.py): bind working directory and session identity; restore persisted histories after reconnect; keep logs out of stdout’s protocol stream.
- [Provider registry](https://github.com/NousResearch/hermes-agent/blob/c8aa5608c24e3636e77c267650c0f1f52e44adb0/agent/provider_registry.py): backend selection is separable from the user-facing agent. Do not mistake a backend’s authentication implementation for provider permission.

## AI Elements

Revision `6a9d5b1822ffb10bba4bd97175f01edd7d8651cd`.

[Prompt input source](https://github.com/vercel/ai-elements/blob/6a9d5b1822ffb10bba4bd97175f01edd7d8651cd/packages/elements/src/prompt-input.tsx) demonstrates composable input regions, attachment limits/cleanup, IME-aware Enter handling, and status-dependent send/stop controls. Translate those interaction ideas into the chosen stack; importing a React component does not implement persistent runs, backend cancellation or permission policy.

## What this foundation adds

A common ARMS work order and evidence model across both agent-runtime and model-endpoint lanes. A small tested ACP transport, three HTTP dialects, a provider policy template, and a composer skill with visual and behavioral contracts. Account readiness and deployed behavior remain separately verified.
