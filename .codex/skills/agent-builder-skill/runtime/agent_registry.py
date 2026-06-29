#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from roundtable_core.agents.factory import (
    AGENT_REGISTRY_SCHEMA,
    DEFAULT_FACTORY_REGISTRY_PATH,
    agent_factory_claim_boundary,
    find_skill_dir,
    iso_now,
    list_factory_agents,
    load_factory_registry,
    register_factory_agent,
    resolve_repo_path,
    set_factory_agent_status,
    validate_factory_registry,
    write_factory_registry,
)


DEFAULT_REGISTRY = DEFAULT_FACTORY_REGISTRY_PATH
REGISTRY_SCHEMA = AGENT_REGISTRY_SCHEMA


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the Agent Factory registry.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Registry JSON path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser("list", help="List registry agents.")
    list_cmd.add_argument("--status", help="Optional status filter.")

    validate_cmd = subparsers.add_parser("validate", help="Validate registry structure and entries.")
    validate_cmd.add_argument("--agent-id", help="Validate a single registry entry.")

    register_cmd = subparsers.add_parser("register", aliases=["add"], help="Register an agent manifest.")
    register_cmd.add_argument("manifest", help="Path to manifest JSON.")
    register_cmd.add_argument("--replace", action="store_true", help="Replace existing agent_id.")
    register_cmd.add_argument("--enable", action="store_true", help="Register directly as enabled; requires skill directory.")

    enable_cmd = subparsers.add_parser("enable", help="Enable a registered agent.")
    enable_cmd.add_argument("agent_id")
    enable_cmd.add_argument(
        "--allow-missing-skill",
        action="store_true",
        help="Allow enable without a local skill directory. Use only for tests.",
    )

    disable_cmd = subparsers.add_parser("disable", help="Disable an agent.")
    disable_cmd.add_argument("agent_id")

    args = parser.parse_args()
    registry_path = resolve_path(args.registry)

    if args.command == "list":
        report = list_agents(registry_path, status=args.status)
    elif args.command == "validate":
        report = validate_registry(registry_path, agent_id=args.agent_id)
    elif args.command in {"register", "add"}:
        report = register_agent(
            registry_path=registry_path,
            manifest_path=resolve_path(args.manifest),
            replace=args.replace,
            enable=args.enable,
        )
    elif args.command == "enable":
        report = set_agent_status(
            registry_path=registry_path,
            agent_id=args.agent_id,
            status="enabled",
            allow_missing_skill=args.allow_missing_skill,
        )
    elif args.command == "disable":
        report = set_agent_status(
            registry_path=registry_path,
            agent_id=args.agent_id,
            status="disabled",
            allow_missing_skill=True,
        )
    else:
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def load_registry(path: Path) -> dict[str, Any]:
    return load_factory_registry(path)


def write_registry(path: Path, payload: dict[str, Any]) -> None:
    write_factory_registry(path, payload)


def list_agents(path: Path, status: str | None = None) -> dict[str, Any]:
    return list_factory_agents(path, status=status)


def validate_registry(path: Path, agent_id: str | None = None) -> dict[str, Any]:
    return validate_factory_registry(path, agent_id=agent_id)


def register_agent(*, registry_path: Path, manifest_path: Path, replace: bool, enable: bool) -> dict[str, Any]:
    return register_factory_agent(
        registry_path=registry_path,
        manifest_path=manifest_path,
        replace=replace,
        enable=enable,
    )


def set_agent_status(
    *,
    registry_path: Path,
    agent_id: str,
    status: str,
    allow_missing_skill: bool,
) -> dict[str, Any]:
    return set_factory_agent_status(
        registry_path=registry_path,
        agent_id=agent_id,
        status=status,
        allow_missing_skill=allow_missing_skill,
    )


def claim_boundary() -> list[str]:
    return agent_factory_claim_boundary()


def resolve_path(path: str | Path) -> Path:
    return resolve_repo_path(path)


if __name__ == "__main__":
    sys.exit(main())
