#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from agent_manifest import load_manifest, resolve_path, validate_manifest_file, validate_manifest_object
from roundtable_core.validation import validate_file


DEFAULT_REGISTRY = REPO_ROOT / "config" / "agent-registry.json"
REGISTRY_SCHEMA = REPO_ROOT / "schemas" / "agent-registry.schema.json"


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
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Registry must be a JSON object: {path}")
    payload.setdefault("schema_version", "0.1.0")
    payload.setdefault("registry_kind", "agent_factory_library")
    payload.setdefault("updated_at", iso_now())
    payload.setdefault("agents", [])
    return payload


def write_registry(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = iso_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_agents(path: Path, status: str | None = None) -> dict[str, Any]:
    registry = load_registry(path)
    agents = [agent for agent in registry.get("agents", []) if isinstance(agent, dict)]
    if status:
        agents = [agent for agent in agents if agent.get("status") == status]
    return {
        "ok": True,
        "action": "agent-registry-list",
        "registry": str(path),
        "agent_count": len(agents),
        "agents": [
            {
                "agent_id": agent.get("agent_id"),
                "short_name": agent.get("short_name"),
                "status": agent.get("status"),
                "source": agent.get("source"),
                "task_types": agent.get("task_types", []),
            }
            for agent in agents
        ],
        "claim_boundary": claim_boundary(),
    }


def validate_registry(path: Path, agent_id: str | None = None) -> dict[str, Any]:
    schema_result = validate_file(schema_path=REGISTRY_SCHEMA, instance_path=path).to_dict()
    registry = load_registry(path)
    agents = [agent for agent in registry.get("agents", []) if isinstance(agent, dict)]
    if agent_id:
        agents = [agent for agent in agents if agent.get("agent_id") == agent_id]
        if not agents:
            return {
                "ok": False,
                "action": "agent-registry-validate",
                "registry": str(path),
                "agent_id": agent_id,
                "errors": [f"agent_id not found: {agent_id}"],
                "schema_validation": schema_result,
            }

    errors = list(schema_result["errors"])
    seen: set[str] = set()
    entry_reports = []
    for agent in agents:
        current_id = str(agent.get("agent_id", ""))
        entry_errors = validate_manifest_object(agent)
        if current_id in seen:
            entry_errors.append(f"duplicate agent_id: {current_id}")
        seen.add(current_id)
        if agent.get("status") == "enabled" and not find_skill_dir(str(agent.get("skill_name", ""))):
            entry_errors.append(f"enabled agent missing local skill directory: {agent.get('skill_name')}")
        entry_reports.append({"agent_id": current_id, "ok": not entry_errors, "errors": entry_errors})
        errors.extend(f"{current_id}: {error}" for error in entry_errors)
    return {
        "ok": not errors,
        "action": "agent-registry-validate",
        "registry": str(path),
        "agent_id": agent_id,
        "agent_count": len(agents),
        "schema_validation": schema_result,
        "entries": entry_reports,
        "errors": errors,
        "claim_boundary": claim_boundary(),
    }


def register_agent(*, registry_path: Path, manifest_path: Path, replace: bool, enable: bool) -> dict[str, Any]:
    manifest_report = validate_manifest_file(manifest_path)
    if not manifest_report["ok"]:
        return {
            "ok": False,
            "action": "agent-register",
            "registry": str(registry_path),
            "manifest": str(manifest_path),
            "errors": manifest_report["errors"],
            "manifest_validation": manifest_report,
        }
    manifest = load_manifest(manifest_path)
    agent_id = str(manifest["agent_id"])
    registry = load_registry(registry_path)
    agents = [agent for agent in registry.get("agents", []) if isinstance(agent, dict)]
    existing_index = next((index for index, agent in enumerate(agents) if agent.get("agent_id") == agent_id), None)
    if existing_index is not None and not replace:
        return {
            "ok": False,
            "action": "agent-register",
            "registry": str(registry_path),
            "agent_id": agent_id,
            "errors": [f"duplicate agent_id: {agent_id}"],
        }
    if enable and not find_skill_dir(str(manifest.get("skill_name", ""))):
        return {
            "ok": False,
            "action": "agent-register",
            "registry": str(registry_path),
            "agent_id": agent_id,
            "errors": [f"cannot enable without local skill directory: {manifest.get('skill_name')}"],
        }
    manifest["status"] = "enabled" if enable else "registered"
    manifest.setdefault("quality", {})
    manifest["quality"]["manifest_valid"] = True
    manifest["quality"]["registry_ready"] = True
    if existing_index is None:
        agents.append(manifest)
    else:
        agents[existing_index] = manifest
    registry["agents"] = sorted(agents, key=lambda item: str(item.get("agent_id", "")))
    write_registry(registry_path, registry)
    return {
        "ok": True,
        "action": "agent-register",
        "registry": str(registry_path),
        "agent_id": agent_id,
        "status": manifest["status"],
        "replaced": existing_index is not None,
        "claim_boundary": claim_boundary(),
    }


def set_agent_status(
    *,
    registry_path: Path,
    agent_id: str,
    status: str,
    allow_missing_skill: bool,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    agents = [agent for agent in registry.get("agents", []) if isinstance(agent, dict)]
    for agent in agents:
        if agent.get("agent_id") != agent_id:
            continue
        if status == "enabled" and not allow_missing_skill and not find_skill_dir(str(agent.get("skill_name", ""))):
            return {
                "ok": False,
                "action": f"agent-{status}",
                "registry": str(registry_path),
                "agent_id": agent_id,
                "errors": [f"cannot enable without local skill directory: {agent.get('skill_name')}"],
            }
        agent["status"] = status
        write_registry(registry_path, registry)
        return {
            "ok": True,
            "action": f"agent-{status}",
            "registry": str(registry_path),
            "agent_id": agent_id,
            "status": status,
            "claim_boundary": claim_boundary(),
        }
    return {
        "ok": False,
        "action": f"agent-{status}",
        "registry": str(registry_path),
        "agent_id": agent_id,
        "errors": [f"agent_id not found: {agent_id}"],
    }


def find_skill_dir(skill_name: str) -> Path | None:
    for root in [REPO_ROOT / ".codex" / "skills", REPO_ROOT / ".claude" / "skills"]:
        candidate = root / skill_name
        if candidate.exists():
            return candidate
    return None


def claim_boundary() -> list[str]:
    return [
        "Agent Factory registry operations are local metadata operations.",
        "They do not claim live Nuwa execution, host-live execution, or provider-live execution.",
    ]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
