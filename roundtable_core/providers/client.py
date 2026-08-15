from __future__ import annotations

import concurrent.futures
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Sequence

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "env_key": "OLLAMA_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "deepseek/deepseek-chat",
        "env_key": "OPENROUTER_API_KEY",
    },
}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def get_default_provider_config(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ProviderConfig:
    chosen_provider = provider or "deepseek"
    if not provider:
        if os.environ.get("DEEPSEEK_API_KEY"):
            chosen_provider = "deepseek"
        elif os.environ.get("OPENAI_API_KEY"):
            chosen_provider = "openai"
        elif os.environ.get("OPENROUTER_API_KEY"):
            chosen_provider = "openrouter"
        elif os.environ.get("OLLAMA_HOST") or os.environ.get("OLLAMA_BASE_URL"):
            chosen_provider = "ollama"

    meta = PROVIDER_DEFAULTS.get(chosen_provider, PROVIDER_DEFAULTS["deepseek"])
    effective_base_url = (
        base_url
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get(f"{chosen_provider.upper()}_BASE_URL")
        or meta["base_url"]
    ).rstrip("/")

    env_key_name = meta["env_key"]
    effective_api_key = (
        api_key
        or os.environ.get(env_key_name)
        or os.environ.get("OPENAI_API_KEY")
        or ( "ollama_dummy_key" if chosen_provider == "ollama" else "" )
    )

    effective_model = model or os.environ.get(f"{chosen_provider.upper()}_MODEL") or meta["default_model"]

    return ProviderConfig(
        provider=chosen_provider,
        base_url=effective_base_url,
        api_key=effective_api_key,
        model=effective_model,
    )


def call_chat_completion(
    messages: list[dict[str, str]],
    config: ProviderConfig,
    *,
    temperature: float = 0.3,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    url = f"{config.base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "RoundTableWorkspace/0.3.0",
    }
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {err.code} from {url}: {err_msg}") from err
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to LLM provider at {url}: {exc}") from exc


def _render_role_system_prompt(role: str) -> str:
    prompts: dict[str, str] = {
        "security-auditor": "You are the Security Auditor. Inspect the code/proposal for OWASP vulnerabilities, credential leaks, auth boundaries, and unsafe inputs. Vote 'ship' only if security risks are zero to negligible, 'revise' if mitigations are needed, 'reject' if critical security flaws exist.",
        "performance-specialist": "You are the Performance Specialist. Inspect for complexity, latency, async bottlenecks, memory leaks, and scaling concerns. Vote 'ship', 'revise', or 'reject'.",
        "api-contract-reviewer": "You are the API Contract Reviewer. Inspect for backward compatibility, breaking changes, schema evolution, and standard HTTP/REST/RPC conventions. Vote 'ship', 'revise', or 'reject'.",
        "database-auditor": "You are the Database & Migration Auditor. Inspect DDL locks, migration safety, rollback readiness, and query indexing. Vote 'ship', 'revise', or 'reject'.",
        "geohot": "You are Geohot (George Hotz lens). Ruthlessly inspect the codebase for bloat, unnecessary abstractions, and redundant layers. Demand minimalist, zero-bloat, direct execution. Vote 'ship', 'revise', or 'reject'.",
        "dario-amodei": "You are Dario Amodei (AI Safety & Capability lens). Inspect for prompt injection vulnerabilities, capability boundary risks, non-determinism, and fail-closed architecture guarantees. Vote 'ship', 'revise', or 'reject'.",
        "martin-fowler": "You are Martin Fowler. Inspect software architecture, refactoring opportunities, domain boundaries, test pyramid health, and anti-cruft patterns. Vote 'ship', 'revise', or 'reject'.",
        "engineering": "You are the Lead Engineer. Inspect implementation elegance, maintainability, test coverage, and blast radius.",
        "risk": "You are the Risk Officer. Inspect worst-case downside, hidden dependencies, and irreversibility.",
        "product": "You are the Product Lead. Inspect user value, clarity of outcomes, and UX consistency.",
    }
    base = prompts.get(role, f"You are the '{role}' reviewer in a multi-perspective decision panel.")
    return (
        f"{base}\n\n"
        "Output your review strictly in JSON with keys:\n"
        "{\n"
        '  "vote": "ship" | "revise" | "reject",\n'
        '  "reason": "1-2 sentence crisp justification for your vote",\n'
        '  "key_concern": "Specific risk or improvement item"\n'
        "}"
    )


def _review_single_role(
    role: str,
    question: str,
    diff_context: str,
    config: ProviderConfig,
) -> dict[str, Any]:
    sys_prompt = _render_role_system_prompt(role)
    user_prompt = f"Target Decision / Question:\n{question}\n\nCode Diff / Context:\n{diff_context}"

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        resp = call_chat_completion(messages, config, temperature=0.2, timeout_seconds=25)
        raw_text = resp["choices"][0]["message"]["content"].strip()
        # Parse JSON if possible
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            vote = str(parsed.get("vote", "revise")).lower()
            if vote not in ("ship", "revise", "reject"):
                vote = "revise"
            return {
                "agent": role,
                "vote": vote,
                "reason": str(parsed.get("reason", raw_text[:120])),
                "key_concern": str(parsed.get("key_concern", "")),
                "model": config.model,
            }
        # Fallback text parsing
        vote = "revise"
        if "vote: ship" in raw_text.lower() or '"vote": "ship"' in raw_text.lower():
            vote = "ship"
        elif "vote: reject" in raw_text.lower() or '"vote": "reject"' in raw_text.lower():
            vote = "reject"
        return {
            "agent": role,
            "vote": vote,
            "reason": raw_text[:160],
            "model": config.model,
        }
    except Exception as exc:
        return {
            "agent": role,
            "vote": "revise",
            "reason": f"Live LLM call error: {exc}",
            "error": str(exc),
        }


def run_live_panel_review(
    question: str,
    diff_context: str,
    roles: Sequence[str],
    config: ProviderConfig,
    *,
    max_workers: int = 5,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(roles), max_workers)) as executor:
        future_to_role = {
            executor.submit(_review_single_role, role, question, diff_context, config): role
            for role in roles
        }
        for future in concurrent.futures.as_completed(future_to_role):
            results.append(future.result())
    return results
