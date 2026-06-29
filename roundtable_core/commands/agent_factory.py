from __future__ import annotations

from pathlib import Path
from typing import Any

from roundtable_core.agents.factory import (
    DEFAULT_FACTORY_REGISTRY_PATH,
    list_factory_agents,
    register_factory_agent,
    resolve_repo_path,
    set_factory_agent_status,
    validate_bundle,
    validate_factory_registry,
)


def resolve_factory_registry_path(registry: str | None = None) -> Path:
    return resolve_repo_path(registry) if registry else DEFAULT_FACTORY_REGISTRY_PATH


def run_agent_list(*, registry: str | None = None, status: str | None = None) -> dict[str, Any]:
    return list_factory_agents(resolve_factory_registry_path(registry), status=status)


def run_agent_validate(
    *,
    registry: str | None = None,
    target: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    if target and looks_like_manifest_path(target):
        return validate_bundle(
            resolve_repo_path(target),
            resolve_repo_path(profile) if profile else None,
        )
    if target:
        return validate_factory_registry(resolve_factory_registry_path(registry), agent_id=target)
    return validate_factory_registry(resolve_factory_registry_path(registry))


def run_agent_register(
    *,
    registry: str | None = None,
    manifest: str,
    replace: bool,
    enable: bool,
) -> dict[str, Any]:
    return register_factory_agent(
        registry_path=resolve_factory_registry_path(registry),
        manifest_path=resolve_repo_path(manifest),
        replace=replace,
        enable=enable,
    )


def run_agent_enable(
    *,
    registry: str | None = None,
    agent_id: str,
    allow_missing_skill: bool,
) -> dict[str, Any]:
    return set_factory_agent_status(
        registry_path=resolve_factory_registry_path(registry),
        agent_id=agent_id,
        status="enabled",
        allow_missing_skill=allow_missing_skill,
    )


def run_agent_disable(*, registry: str | None = None, agent_id: str) -> dict[str, Any]:
    return set_factory_agent_status(
        registry_path=resolve_factory_registry_path(registry),
        agent_id=agent_id,
        status="disabled",
        allow_missing_skill=True,
    )


def looks_like_manifest_path(target: str) -> bool:
    return target.endswith(".json") or "/" in target or "\\" in target
