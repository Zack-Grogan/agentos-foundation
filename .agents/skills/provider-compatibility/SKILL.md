---
name: provider-compatibility
description: Research and implement subscription-aware ACP or native agent adapters and explicit OpenAI or Anthropic-compatible API endpoints without conflating authentication, entitlement and transport.
---

Read [the compatibility guide](../../../docs/providers.md) and [source patterns](../../../docs/provider-patterns.md).

1. Identify the exact provider instance, desired agent/model lane and source of authority for credentials.
2. Verify current official documentation, installed version, supported transport and account entitlement independently.
3. Record native versus bridged ACP, authentication owner, billing route, model capabilities and policy restrictions.
4. Use an isolated project runtime; never assume ACP capability flags sandbox native tools or block inherited hooks.
5. Add one opt-in adapter with explicit limits and no automatic login, billing fallback or credential copying.
6. Test protocol normalization with fixtures, then an authorized live prompt, cancellation/denial and restart. Keep evidence levels explicit.
7. Update the dated compatibility matrix and provider contract; preserve original source references and unresolved differences.
