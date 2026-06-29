#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.agents.factory import (
    PROFILE_REQUIRED_MARKERS,
    infer_profile_path,
    load_manifest,
    load_manifest_schema,
    normalize_manifest,
    resolve_repo_path,
    slugify,
    validate_manifest_file,
    validate_manifest_object,
    validate_manifest_semantics,
    validate_profile,
)


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
    return resolve_repo_path(path)


def print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
