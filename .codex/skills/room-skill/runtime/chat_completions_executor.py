#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class ProviderConfigError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    env = dict(os.environ)
    if args.env_file:
        env.update(load_env_file(Path(args.env_file)))

    try:
        config = read_provider_config(env)
        if args.check_provider_config:
            payload = {
                "ready": True,
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
        description="Call a Chat Completions-compatible provider for checked-in /room prompt files."
    )
    parser.add_argument("--env-file", help="Optional explicit .env file for provider config.")
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


def read_provider_config(env: dict[str, str]) -> dict[str, Any]:
    url = env.get("ROOM_CHAT_COMPLETIONS_URL", "").strip()
    model = env.get("ROOM_CHAT_COMPLETIONS_MODEL", "").strip()
    auth_bearer = (
        env.get("ROOM_PROVIDER_AUTH_BEARER", "").strip()
        or env.get("ROOM_PROVIDER_API_KEY", "").strip()
        or env.get("OPENAI_API_KEY", "").strip()
    )
    timeout_raw = env.get("ROOM_PROVIDER_TIMEOUT_SECONDS", "").strip() or "60"
    if not url:
        raise ProviderConfigError("Missing ROOM_CHAT_COMPLETIONS_URL.")
    if not model:
        raise ProviderConfigError("Missing ROOM_CHAT_COMPLETIONS_MODEL.")
    try:
        timeout_seconds = int(timeout_raw)
    except ValueError as exc:
        raise ProviderConfigError("ROOM_PROVIDER_TIMEOUT_SECONDS must be an integer.") from exc
    return {
        "url": url,
        "model": model,
        "auth_bearer": auth_bearer,
        "timeout_seconds": timeout_seconds,
    }


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
