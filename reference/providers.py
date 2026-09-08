"""Explicit workspace provider configuration; diagnostics never log in or run agents."""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from adapters.http_models import Endpoint
from .core import Invalid, digest

ROOT = Path(__file__).resolve().parents[1]
LOCAL = {
    "id": "local",
    "transport": "deterministic",
    "enabled": True,
    "timeout_seconds": 10,
}


def configs(store):
    path = store.directory / "providers.json"
    if path.is_symlink():
        raise Invalid("Provider configuration must not be a symlink.")
    if not path.exists():
        return [LOCAL]
    if not path.is_file() or path.stat().st_size > 65536:
        raise Invalid(
            "Provider configuration must be a bounded regular workspace file."
        )
    value = json.loads(path.read_text())
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "instances"}
        or value["version"] != 1
        or not isinstance(value["instances"], list)
        or len(value["instances"]) > 20
    ):
        raise Invalid(
            "Invalid providers.json structure; use templates/runtime-providers.json."
        )
    seen = {"local"}
    result = [LOCAL]
    for item in value["instances"]:
        if (
            not isinstance(item, dict)
            or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", str(item.get("id", "")))
            or item["id"] in seen
        ):
            raise Invalid("Provider IDs must be unique lowercase names.")
        seen.add(item["id"])
        if type(item.get("enabled")) is not bool:
            raise Invalid("Provider enabled must be a boolean.")
        common = {"id", "transport", "enabled", "timeout_seconds"}
        if (
            type(item.get("timeout_seconds")) is not int
            or not 1 <= item["timeout_seconds"] <= 300
        ):
            raise Invalid("Provider timeout must be 1–300 seconds.")
        if item.get("transport") in (
            "openai-chat",
            "openai-responses",
            "anthropic-messages",
        ):
            allowed = common | {
                "base_url",
                "model",
                "key_env",
                "max_output_tokens",
                "allow_loopback_http",
            }
            if set(item) - allowed or not {"base_url", "model", "key_env"} <= set(item):
                raise Invalid("Unexpected/missing endpoint configuration fields.")
            if (
                not all(
                    isinstance(item[k], str) for k in ("base_url", "model", "key_env")
                )
                or type(item.get("allow_loopback_http", False)) is not bool
            ):
                raise Invalid("Endpoint values must have the expected types.")
            Endpoint(
                item["base_url"],
                item["transport"],
                item["model"],
                item["key_env"],
                item["timeout_seconds"],
                item.get("max_output_tokens", 2048),
                item.get("allow_loopback_http", False),
            ).validate()
        elif item.get("transport") == "acp":
            allowed = common | {
                "command",
                "env_refs",
                "scope_reviewed",
                "auth_owned_by_user",
            }
            if (
                set(item) != allowed
                or not isinstance(item["command"], list)
                or not item["command"]
                or len(item["command"]) > 30
                or not all(
                    isinstance(a, str) and 0 < len(a) <= 2000 for a in item["command"]
                )
            ):
                raise Invalid(
                    "ACP needs an explicit executable argument vector and isolation acknowledgments."
                )
            if (
                not Path(item["command"][0]).is_absolute()
                or not isinstance(item["env_refs"], dict)
                or len(item["env_refs"]) > 30
            ):
                raise Invalid(
                    "ACP executable must be absolute and env_refs must name explicit environment variables."
                )
            if not all(
                isinstance(k, str)
                and k.isidentifier()
                and isinstance(v, str)
                and v.isidentifier()
                for k, v in item["env_refs"].items()
            ):
                raise Invalid(
                    "ACP environment values must be variable names, never credentials."
                )
            if any(
                type(item[k]) is not bool
                for k in ("scope_reviewed", "auth_owned_by_user")
            ):
                raise Invalid("ACP scope acknowledgments must be booleans.")
            forbidden = {
                "PYTHONPATH",
                "PYTHONHOME",
                "PYTHONSTARTUP",
                "LD_PRELOAD",
                "DYLD_INSERT_LIBRARIES",
            }
            if (
                set(item["env_refs"]) & forbidden
                or set(item["env_refs"].values()) & forbidden
            ):
                raise Invalid("Runtime loader environment overrides are not supported.")
            if item["enabled"] and not (
                item["scope_reviewed"] and item["auth_owned_by_user"]
            ):
                raise Invalid(
                    "Review native process scope and user-owned authentication before enabling ACP."
                )
        else:
            raise Invalid("Unsupported provider transport.")
        result.append(item)
    return result


def selected(store, provider_id):
    item = next((x for x in configs(store) if x["id"] == provider_id), None)
    if item is None or not item["enabled"]:
        raise Invalid("Selected provider is missing or disabled.")
    return item


def diagnostics(store):
    result = []
    error = None
    try:
        available = configs(store)
    except (ValueError, TypeError, AttributeError, OSError):
        available = [LOCAL]
        error = (
            "Invalid providers.json. Local work is available; repair provider setup."
        )
    for c in available:
        status = "ready-local" if c["id"] == "local" else "disabled"
        if c["enabled"] and c["id"] != "local":
            if c["transport"] == "acp":
                present = Path(c["command"][0]).is_file() and os.access(
                    c["command"][0], os.X_OK
                )
                env_ok = all(
                    os.environ.get(v) is not None for v in c["env_refs"].values()
                )
                status = (
                    "configured-unverified" if present and env_ok else "setup-required"
                )
            else:
                status = (
                    "configured-unverified"
                    if os.environ.get(c["key_env"])
                    else "credential-missing"
                )
        result.append(
            {
                "id": c["id"],
                "transport": c["transport"],
                "enabled": c["enabled"],
                "status": status,
                "configuration_digest": digest(c),
            }
        )
    return {
        "python": sys.version.split()[0],
        "schema_version": 2,
        "instances": result,
        "configuration_error": error,
        "cli_present": {
            name: bool(shutil.which(name))
            for name in ("claude", "codex", "grok", "cursor-agent", "hermes")
        },
        "note": "Static checks only. No credential values, login, session, model probe or home configuration was read.",
    }
