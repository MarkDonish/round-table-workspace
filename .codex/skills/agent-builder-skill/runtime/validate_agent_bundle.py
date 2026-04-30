#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from agent_manifest import infer_profile_path, load_manifest, resolve_path, validate_manifest_file, validate_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Factory bundle.")
    parser.add_argument("manifest", help="Path to agent.manifest.json or *.agent.manifest.json.")
    parser.add_argument("--profile", help="Path to roundtable-profile.md. If omitted, infer beside manifest.")
    args = parser.parse_args()

    report = validate_bundle(resolve_path(args.manifest), resolve_path(args.profile) if args.profile else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def validate_bundle(manifest_path: Path, profile_path: Path | None = None) -> dict[str, object]:
    manifest_report = validate_manifest_file(manifest_path)
    manifest = None
    try:
        manifest = load_manifest(manifest_path)
    except Exception:
        manifest = None
    resolved_profile = profile_path or infer_profile_path(manifest_path, manifest)
    profile_report = validate_profile(resolved_profile) if resolved_profile else {
        "ok": False,
        "errors": ["profile could not be inferred"],
    }
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


if __name__ == "__main__":
    sys.exit(main())
