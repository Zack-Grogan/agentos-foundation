"""Bounded text-only OpenAI/Anthropic dialect clients; no implicit billing fallback."""
import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError


class ProviderError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


@dataclass(frozen=True)
class Endpoint:
    base_url: str
    dialect: str  # openai-chat, openai-responses, anthropic-messages
    model: str
    key_env: str
    timeout_seconds: float = 30
    max_output_tokens: int = 1024
    allow_loopback_http: bool = False

    def validate(self):
        url = urlsplit(self.base_url)
        local_http = self.allow_loopback_http and url.scheme == "http" and url.hostname in ("127.0.0.1", "::1", "localhost")
        if (url.scheme != "https" and not local_http) or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ProviderError("Use an explicit HTTPS base URL, or opt into loopback HTTP.")
        if self.dialect not in ("openai-chat", "openai-responses", "anthropic-messages"):
            raise ProviderError("Choose an explicit supported API dialect.")
        if not self.model.strip() or not self.key_env.isidentifier():
            raise ProviderError("A model ID and credential environment-variable name are required.")
        if not 0 < self.timeout_seconds <= 300 or type(self.max_output_tokens) is not int or not 1 <= self.max_output_tokens <= 32768:
            raise ProviderError("Invalid request limits.")


def build_request(config, prompt, system=""):
    config.validate()
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 60000 or not isinstance(system, str) or len(system) > 20000:
        raise ProviderError("Expected bounded nonempty text input.")
    key = os.environ.get(config.key_env)
    if not key:
        raise ProviderError("Configured credential environment variable is unset.")
    headers = {"Content-Type": "application/json"}
    common = {"model": config.model, "stream": False}
    if config.dialect == "openai-chat":
        path = "/chat/completions"
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {**common, "messages": messages, "max_completion_tokens": config.max_output_tokens}
        headers["Authorization"] = "Bearer " + key
    elif config.dialect == "openai-responses":
        path = "/responses"
        body = {**common, "input": prompt, "max_output_tokens": config.max_output_tokens, "store": False}
        if system:
            body["instructions"] = system
        headers["Authorization"] = "Bearer " + key
    else:
        path = "/messages"
        body = {**common, "messages": [{"role": "user", "content": prompt}], "max_tokens": config.max_output_tokens}
        if system:
            body["system"] = system
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    return Request(config.base_url.rstrip("/") + path, data=json.dumps(body).encode(), headers=headers, method="POST")


def parse_response(dialect, response):
    try:
        if dialect == "openai-chat":
            choice = response["choices"][0]
            if choice.get("finish_reason") != "stop" or choice["message"].get("tool_calls"):
                raise ProviderError("Response is incomplete or requires unsupported tools.")
            text = choice["message"]["content"]
        elif dialect == "openai-responses":
            if response.get("status") != "completed":
                raise ProviderError("Response did not complete.")
            output = response["output"]
            if any(item.get("type") not in ("message", "reasoning") for item in output):
                raise ProviderError("Response requires an unsupported tool or output type.")
            text = "".join(part["text"] for item in output if item.get("type") == "message"
                           for part in item.get("content", []) if part.get("type") == "output_text")
        elif dialect == "anthropic-messages":
            if response.get("stop_reason") != "end_turn" or any(part.get("type") != "text" for part in response["content"]):
                raise ProviderError("Response is incomplete or not text-only.")
            text = "".join(part["text"] for part in response["content"])
        else:
            raise ProviderError("Unsupported API dialect.")
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Provider returned no usable text.")
        return {"text": text, "usage": response.get("usage"), "provider_response_id": response.get("id")}
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ProviderError("Unexpected provider response shape.") from exc


def complete(config, prompt, system=""):
    request = build_request(config, prompt, system)
    # Redirects and ambient proxy settings do not silently change credential destination.
    opener = build_opener(NoRedirect(), ProxyHandler({}))
    try:
        with opener.open(request, timeout=config.timeout_seconds) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ProviderError("Provider response exceeded size limit.")
        return parse_response(config.dialect, json.loads(raw))
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ProviderError(f"Provider HTTP {code}; no automatic retry or fallback.") from None
    except (URLError, TimeoutError) as exc:
        raise ProviderError("Provider transport failed; billing/outcome may be unknown.") from None
    except (ValueError, UnicodeDecodeError):
        raise ProviderError("Provider returned invalid JSON.") from None
