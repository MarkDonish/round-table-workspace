from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from roundtable_core.runtime.paths import UnsafePathError, assert_no_symlink_components
from roundtable_core.validation import validate_file, validate_instance


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FACTORY_REGISTRY_PATH = REPO_ROOT / "config" / "agent-registry.json"
AGENT_REGISTRY_SCHEMA = REPO_ROOT / "schemas" / "agent-registry.schema.json"
AGENT_MANIFEST_SCHEMA = REPO_ROOT / "schemas" / "agent-manifest.schema.json"

PROFILE_REQUIRED_MARKERS = [
    "# Roundtable Profile:",
    "agent_id:",
    "short_name:",
    "skill_name:",
    "source:",
    "status:",
    "## Cognitive Lens",
    "## Primary Role",
    "## Best For",
    "## Should Not Lead",
    "## Discussion Style",
    "## Bias Risk",
    "## Counterweights",
]


def resolve_repo_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    return payload


def load_manifest_schema() -> dict[str, Any]:
    return json.loads(AGENT_MANIFEST_SCHEMA.read_text(encoding="utf-8"))


def validate_manifest_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "ok": False,
            "action": "agent-manifest-validate",
            "manifest": str(path),
            "agent_id": None,
            "schema_validation": None,
            "semantic_errors": [],
            "errors": [f"manifest does not exist: {path}"],
        }
    schema_result = validate_file(schema_path=AGENT_MANIFEST_SCHEMA, instance_path=path).to_dict()
    semantic_errors: list[str] = []
    manifest: dict[str, Any] | None = None
    try:
        manifest = normalize_manifest(load_manifest(path))
        semantic_errors.extend(validate_manifest_semantics(manifest))
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        semantic_errors.append(str(exc))

    errors = list(schema_result["errors"]) + semantic_errors
    return {
        "ok": not errors,
        "action": "agent-manifest-validate",
        "manifest": str(path),
        "agent_id": manifest.get("agent_id") if manifest else None,
        "schema_validation": schema_result,
        "semantic_errors": semantic_errors,
        "errors": errors,
    }


def validate_manifest_object(manifest: dict[str, Any]) -> list[str]:
    schema = load_manifest_schema()
    errors = validate_instance(instance=manifest, schema=schema)
    errors.extend(validate_manifest_semantics(normalize_manifest(manifest)))
    return errors


def normalize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(manifest)
    for key in ["useful_when", "avoid", "task_types", "stage_fit", "sub_problem_tags", "counterweights"]:
        value = normalized.get(key)
        if isinstance(value, tuple):
            normalized[key] = list(value)
    return normalized


def validate_manifest_semantics(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    agent_id = manifest.get("agent_id")
    if isinstance(agent_id, str) and slugify(agent_id) != agent_id:
        errors.append("agent_id must already be normalized as a lowercase hyphen slug")
    if not manifest.get("style_rule"):
        errors.append("style_rule is required to prevent voice imitation")
    if not manifest.get("bias_risk"):
        errors.append("bias_risk is required")
    counterweights = manifest.get("counterweights")
    if not isinstance(counterweights, list) or not counterweights:
        errors.append("counterweights must contain at least one balancing lens")
    avoid = manifest.get("avoid")
    avoid_text = " ".join(str(item).lower() for item in avoid) if isinstance(avoid, list) else ""
    if "voice imitation" not in avoid_text and "imitat" not in str(manifest.get("style_rule", "")).lower():
        errors.append("manifest must explicitly guard against voice imitation")
    return errors


def validate_profile(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"profile does not exist: {path}")
        return {
            "ok": False,
            "action": "roundtable-profile-validate",
            "profile": str(path),
            "errors": errors,
        }
    text = path.read_text(encoding="utf-8")
    for marker in PROFILE_REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"profile missing required marker: {marker}")
    return {
        "ok": not errors,
        "action": "roundtable-profile-validate",
        "profile": str(path),
        "required_markers": PROFILE_REQUIRED_MARKERS,
        "errors": errors,
    }


def infer_profile_path(manifest_path: Path, manifest: dict[str, Any] | None = None) -> Path | None:
    candidates = []
    name = manifest_path.name
    if name.endswith(".agent.manifest.json"):
        candidates.append(manifest_path.with_name(name.replace(".agent.manifest.json", ".roundtable-profile.md")))
    candidates.append(manifest_path.parent / "roundtable-profile.md")
    if manifest and isinstance(manifest.get("agent_id"), str):
        candidates.append(manifest_path.parent / f"{manifest['agent_id']}.roundtable-profile.md")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def validate_bundle(manifest_path: Path, profile_path: Path | None = None) -> dict[str, object]:
    manifest_report = validate_manifest_file(manifest_path)
    manifest = None
    try:
        manifest = load_manifest(manifest_path)
    except Exception:
        manifest = None
    resolved_profile = profile_path or infer_profile_path(manifest_path, manifest)
    profile_report = (
        validate_profile(resolved_profile)
        if resolved_profile
        else {
            "ok": False,
            "errors": ["profile could not be inferred"],
        }
    )
    return {
        "ok": bool(manifest_report["ok"] and profile_report["ok"]),
        "action": "agent-bundle-validate",
        "manifest": str(manifest_path),
        "profile": str(resolved_profile) if resolved_profile else None,
        "agent_id": manifest_report.get("agent_id"),
        "manifest_validation": manifest_report,
        "profile_validation": profile_report,
        "claim_boundary": [
            "This validates local Agent Factory bundle structure only.",
            "It does not claim live Nuwa execution, host-live execution, or provider-live execution.",
        ],
    }


def load_factory_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Registry must be a JSON object: {path}")
    payload.setdefault("schema_version", "0.1.0")
    payload.setdefault("registry_kind", "agent_factory_library")
    payload.setdefault("updated_at", iso_now())
    payload.setdefault("agents", [])
    return payload


def write_factory_registry(path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing to write registry through symlink: {path}")
    try:
        assert_no_symlink_components(path, include_leaf=False)
    except UnsafePathError as exc:
        raise ValueError(f"Refusing to write registry through symlink component: {exc}") from exc
    payload["updated_at"] = iso_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temp_file = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(temp_file.name)
    try:
        with temp_file:
            temp_file.write(data)
            temp_file.flush()
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def list_factory_agents(path: Path, status: str | None = None) -> dict[str, Any]:
    if not path.exists():
        return missing_registry_report("agent-registry-list", path)
    registry = load_factory_registry(path)
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
        "claim_boundary": agent_factory_claim_boundary(),
    }


def validate_factory_registry(path: Path, agent_id: str | None = None) -> dict[str, Any]:
    if not path.exists():
        report = missing_registry_report("agent-registry-validate", path)
        report["agent_id"] = agent_id
        return report
    schema_result = validate_file(schema_path=AGENT_REGISTRY_SCHEMA, instance_path=path).to_dict()
    registry = load_factory_registry(path)
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
        "claim_boundary": agent_factory_claim_boundary(),
    }


def register_factory_agent(*, registry_path: Path, manifest_path: Path, replace: bool, enable: bool) -> dict[str, Any]:
    if not registry_path.exists():
        return missing_registry_report("agent-register", registry_path)
    try:
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
        registry = load_factory_registry(registry_path)
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
        write_factory_registry(registry_path, registry)
        return {
            "ok": True,
            "action": "agent-register",
            "registry": str(registry_path),
            "agent_id": agent_id,
            "status": manifest["status"],
            "replaced": existing_index is not None,
            "claim_boundary": agent_factory_claim_boundary(),
        }
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "action": "agent-register",
            "registry": str(registry_path),
            "manifest": str(manifest_path),
            "errors": [str(exc)],
        }


def set_factory_agent_status(
    *,
    registry_path: Path,
    agent_id: str,
    status: str,
    allow_missing_skill: bool,
) -> dict[str, Any]:
    if not registry_path.exists():
        return missing_registry_report(f"agent-{status}", registry_path)
    try:
        registry = load_factory_registry(registry_path)
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
            write_factory_registry(registry_path, registry)
            return {
                "ok": True,
                "action": f"agent-{status}",
                "registry": str(registry_path),
                "agent_id": agent_id,
                "status": status,
                "claim_boundary": agent_factory_claim_boundary(),
            }
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "action": f"agent-{status}",
            "registry": str(registry_path),
            "agent_id": agent_id,
            "errors": [str(exc)],
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


def agent_factory_claim_boundary() -> list[str]:
    return [
        "Agent Factory registry operations are local metadata operations.",
        "They do not claim live Nuwa execution, host-live execution, or provider-live execution.",
    ]


def missing_registry_report(action: str, path: Path) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "registry": str(path),
        "errors": [f"registry does not exist: {path}"],
        "claim_boundary": agent_factory_claim_boundary(),
    }


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-")


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
