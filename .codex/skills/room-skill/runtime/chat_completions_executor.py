#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any


class ProviderConfigError(Exception):
    pass


PLACEHOLDER_EXACT_VALUES = {
    "EMPTY",
    "your-model-name",
    "your-provider-token",
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    env = dict(os.environ)
    if args.env_file:
        env.update(load_env_file(Path(args.env_file)))

    try:
        config = read_provider_config(env, provider_scope=args.provider_scope)
        if args.check_provider_config:
            payload = {
                "ready": True,
                "provider_scope": args.provider_scope,
                "url": mask_value(config["url"]),
                "model": mask_value(config["model"]),
                "auth_configured": bool(config.get("auth_bearer")),
                "timeout_seconds": config["timeout_seconds"],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
        prompt_input = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        result = call_chat_completions(
            config=config,
            prompt_text=prompt_text,
            prompt_input=prompt_input,
            temperature=args.temperature,
        )

        output_json = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output_json:
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_json, encoding="utf-8")
        else:
            sys.stdout.write(output_json)
        return 0
    except (ProviderConfigError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call a Chat Completions-compatible provider for checked-in runtime prompt files."
    )
    parser.add_argument("--env-file", help="Optional explicit .env file for provider config.")
    parser.add_argument(
        "--provider-scope",
        choices=["room", "debate"],
        default="room",
        help="Which checked-in runtime scope to read provider variables for.",
    )
    parser.add_argument("--check-provider-config", action="store_true")
    parser.add_argument("--prompt-file", help="Prompt markdown file.")
    parser.add_argument("--input-json", help="JSON input file for the prompt.")
    parser.add_argument("--output-json", help="Optional path for the parsed JSON output.")
    parser.add_argument("--temperature", type=float, default=0.1)
    return parser


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ProviderConfigError(f"Env file does not exist: {path}")
    loaded: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        loaded[key] = value
    return loaded


def read_provider_config(env: dict[str, str], *, provider_scope: str = "room") -> dict[str, Any]:
    if provider_scope == "room":
        primary_prefix = "ROOM"
        fallback_prefixes: tuple[str, ...] = ()
    elif provider_scope == "debate":
        primary_prefix = "DEBATE"
        fallback_prefixes = ("ROOM",)
    else:
        raise ProviderConfigError(f"Unsupported provider scope: {provider_scope}")

    url = get_first_env(env, provider_keys(primary_prefix, "CHAT_COMPLETIONS_URL", fallback_prefixes))
    model = get_first_env(env, provider_keys(primary_prefix, "CHAT_COMPLETIONS_MODEL", fallback_prefixes))
    auth_bearer = (
        get_first_env(env, provider_keys(primary_prefix, "PROVIDER_AUTH_BEARER", fallback_prefixes))
        or get_first_env(env, provider_keys(primary_prefix, "PROVIDER_API_KEY", fallback_prefixes))
        or env.get("OPENAI_API_KEY", "").strip()
    )
    timeout_raw = get_first_env(env, provider_keys(primary_prefix, "PROVIDER_TIMEOUT_SECONDS", fallback_prefixes)) or "60"
    if not url:
        raise ProviderConfigError(missing_config_message(primary_prefix, "CHAT_COMPLETIONS_URL", fallback_prefixes))
    if not model:
        raise ProviderConfigError(missing_config_message(primary_prefix, "CHAT_COMPLETIONS_MODEL", fallback_prefixes))
    ensure_non_placeholder_config_value(url, f"{primary_prefix}_CHAT_COMPLETIONS_URL")
    ensure_non_placeholder_config_value(model, f"{primary_prefix}_CHAT_COMPLETIONS_MODEL")
    if auth_bearer:
        ensure_non_placeholder_config_value(auth_bearer, f"{primary_prefix}_PROVIDER_AUTH_BEARER")
    try:
        timeout_seconds = int(timeout_raw)
    except ValueError as exc:
        raise ProviderConfigError(f"{primary_prefix}_PROVIDER_TIMEOUT_SECONDS must be an integer.") from exc
    return {
        "url": url,
        "model": model,
        "auth_bearer": auth_bearer,
        "timeout_seconds": timeout_seconds,
        "provider_scope": provider_scope,
    }


def ensure_non_placeholder_config_value(value: str, key: str) -> None:
    stripped = value.strip()
    if not stripped:
        return
    if stripped in PLACEHOLDER_EXACT_VALUES:
        raise ProviderConfigError(f"{key} is still using the example placeholder value `{stripped}`.")
    if key.endswith("_CHAT_COMPLETIONS_URL"):
        parsed = urllib.parse.urlparse(stripped)
        if parsed.hostname and parsed.hostname.endswith(".example"):
            raise ProviderConfigError(f"{key} is still using the example placeholder URL `{stripped}`.")


def provider_keys(primary_prefix: str, suffix: str, fallback_prefixes: tuple[str, ...]) -> list[str]:
    return [f"{primary_prefix}_{suffix}", *[f"{prefix}_{suffix}" for prefix in fallback_prefixes]]


def get_first_env(env: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = env.get(key, "").strip()
        if value:
            return value
    return ""


def missing_config_message(primary_prefix: str, suffix: str, fallback_prefixes: tuple[str, ...]) -> str:
    primary_key = f"{primary_prefix}_{suffix}"
    if not fallback_prefixes:
        return f"Missing {primary_key}."
    fallback_text = ", ".join(f"{prefix}_{suffix}" for prefix in fallback_prefixes)
    return f"Missing {primary_key}. Fallbacks checked: {fallback_text}."


def call_chat_completions(
    *,
    config: dict[str, Any],
    prompt_text: str,
    prompt_input: dict[str, Any],
    temperature: float,
) -> dict[str, Any]:
    body = {
        "model": config["model"],
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Follow the checked-in prompt exactly. "
                    "Return strict JSON only, with no prose outside the JSON.\n\n"
                    + prompt_text
                ),
            },
            {
                "role": "user",
                "content": (
                    "Use this structured input and produce the required JSON output only.\n\n"
                    "```json\n"
                    + json.dumps(prompt_input, ensure_ascii=False, indent=2)
                    + "\n```"
                ),
            },
        ],
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if config.get("auth_bearer"):
        headers["Authorization"] = f"Bearer {config['auth_bearer']}"

    request = urllib.request.Request(config["url"], data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=config["timeout_seconds"]) as response:
        raw = response.read().decode("utf-8")

    response_json = json.loads(raw)
    content = extract_message_content(response_json)
    return parse_json_from_text(content)


def extract_message_content(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderConfigError("Provider response missing choices[0].")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ProviderConfigError("Provider response missing choices[0].message.")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        joined = "".join(text_parts).strip()
        if joined:
            return joined
    raise ProviderConfigError("Provider response did not contain text content.")


def parse_json_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ProviderConfigError("Prompt result must be a JSON object.")
        return parsed
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", stripped, re.DOTALL)
        if not match:
            raise ProviderConfigError("Provider response did not contain a parseable JSON object.")
        parsed = json.loads(match.group(1))
        if not isinstance(parsed, dict):
            raise ProviderConfigError("Prompt result must be a JSON object.")
        return parsed


def mask_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "..." + value[-4:]


if __name__ == "__main__":
    sys.exit(main())
