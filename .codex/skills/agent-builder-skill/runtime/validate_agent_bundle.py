#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from roundtable_core.agents.factory import resolve_repo_path, validate_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Factory bundle.")
    parser.add_argument("manifest", help="Path to agent.manifest.json or *.agent.manifest.json.")
    parser.add_argument("--profile", help="Path to roundtable-profile.md. If omitted, infer beside manifest.")
    args = parser.parse_args()

    report = validate_bundle(resolve_path(args.manifest), resolve_path(args.profile) if args.profile else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def resolve_path(path: str | Path) -> Path:
    return resolve_repo_path(path)


if __name__ == "__main__":
    sys.exit(main())
