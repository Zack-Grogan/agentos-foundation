# Opt-in transport modules

These modules are independent of the default reference server. They are tested against controlled peers and have **not** been verified with live subscriber accounts. Read `docs/providers.md` before integrating them.

## Model endpoints

`http_models.Endpoint` selects exactly one of `openai-chat`, `openai-responses`, or `anthropic-messages`. The base URL includes the desired prefix (usually `/v1`). `key_env` names a credential; it never contains the credential itself. `complete` makes one bounded non-streaming text request and returns text, raw reported usage or null, and provider response ID.

```python
from adapters.http_models import Endpoint, complete
# Only run after selecting and authorizing this API billing/data route.
endpoint = Endpoint(
    base_url="https://your-authorized-provider.example/v1",
    dialect="anthropic-messages",
    model="your-verified-model-id",
    key_env="AGENTOS_MODEL_API_KEY",
)
# result = complete(endpoint, "Your selected input")
```

HTTPS is required except explicit loopback HTTP. Redirects and ambient proxies are disabled to keep credentials at the selected destination. No retries or billing fallback. Text-only subset; tool responses and incomplete output fail explicitly. HTTP socket timeout and response byte limits are provided; a production runner must additionally impose a total wall-clock deadline (a slow trickle can outlive a socket inactivity timeout).

## ACP

`acp.ACPClient` accepts an **absolute** executable argument vector, absolute workspace, and explicit environment. `start` initializes only; authentication is caller-owned and must use advertised methods after authorization. `new_session`, `prompt`, `cancel` and `close` provide the basic flow. `updates` contains bounded native session updates; production ingestion should normalize/persist them as they arrive. Always `close` in a `finally` block.

All incoming permission requests are denied/cancelled; unsupported client requests get a method-not-found response. No client filesystem or terminal capabilities are advertised. This does **not** confine native agent tools or startup hooks. The embedding application must establish native settings, account isolation and an OS sandbox appropriate to its scope. The module does not create a browser login, search personal credentials, install packages or load global skills.

No provider-specific extension UI, session restoration UI, native Codex App Server driver or distributed job supervisor is included. Cursor blocking extensions require a real client implementation before enabling those flows. On POSIX, close terminates the subprocess group; Windows production process-tree containment requires a job object or equivalent.

`templates/providers.json` is a disabled planning manifest, not an executable launcher configuration. Pin installed adapter versions and replace executable placeholders after verification.
