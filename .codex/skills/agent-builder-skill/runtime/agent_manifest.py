#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.validation import validate_file, validate_instance


MANIFEST_SCHEMA = REPO_ROOT / "schemas" / "agent-manifest.schema.json"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and normalize Agent Factory manifests.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate one agent manifest file.")
    validate.add_argument("manifest")

    normalize = subparsers.add_parser("normalize", help="Print normalized manifest JSON.")
    normalize.add_argument("manifest")

    slug = subparsers.add_parser("slug", help="Render a stable agent_id slug from text.")
    slug.add_argument("text")

    args = parser.parse_args()
    if args.command == "validate":
        report = validate_manifest_file(resolve_path(args.manifest))
        print_json(report)
        return 0 if report["ok"] else 1
    if args.command == "normalize":
        manifest = normalize_manifest(load_manifest(resolve_path(args.manifest)))
        print_json(manifest)
        return 0
    if args.command == "slug":
        print(slugify(args.text))
        return 0
    return 2


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (REPO_ROOT / candidate).resolve()


def print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    return payload


def load_manifest_schema() -> dict[str, Any]:
    return json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))


def validate_manifest_file(path: Path) -> dict[str, Any]:
    schema_result = validate_file(schema_path=MANIFEST_SCHEMA, instance_path=path).to_dict()
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


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-")


if __name__ == "__main__":
    sys.exit(main())
