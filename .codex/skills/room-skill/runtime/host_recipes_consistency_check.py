#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import agent_host_inventory


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
HOST_RECIPES_DOC = REPO_ROOT / "docs/local-agent-host-recipes.md"
QUICKSTART_DOC = REPO_ROOT / "docs/agent-consumer-quickstart.md"
LAUNCH_DOC = REPO_ROOT / "LAUNCH.md"

REQUIRED_HOST_RECIPE_PHRASES = [
    "matrix_status=live_passed",
    "provider URLs are not required",
    "fixture validation is not host-live evidence",
    "docs/third-party-agent-wrapper-recipes.md",
]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_report()
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check that local agent host recipe docs cover every checked-in host "
            "candidate and preserve release-scope claim boundaries."
        )
    )
    parser.add_argument("--output-json", help="Optional path to persist the consistency report.")
    return parser


def build_report() -> dict[str, Any]:
    docs = {
        "host_recipes": read_doc(HOST_RECIPES_DOC),
        "quickstart": read_doc(QUICKSTART_DOC),
        "launch": read_doc(LAUNCH_DOC),
    }
    host_checks = [check_host(candidate, docs["host_recipes"]) for candidate in agent_host_inventory.CANDIDATES]
    host_recipes_lower = docs["host_recipes"].lower()
    phrase_checks = [
        {"phrase": phrase, "present": phrase.lower() in host_recipes_lower}
        for phrase in REQUIRED_HOST_RECIPE_PHRASES
    ]
    cross_links = {
        "quickstart_links_host_recipes": "docs/local-agent-host-recipes.md" in docs["quickstart"],
        "launch_links_host_recipes": "docs/local-agent-host-recipes.md" in docs["launch"],
    }
    missing = {
        "hosts": [item for item in host_checks if not item["present"]],
        "phrases": [item for item in phrase_checks if not item["present"]],
        "cross_links": [name for name, present in cross_links.items() if not present],
    }
    return {
        "ok": not any(missing.values()),
        "action": "host-recipes-consistency-check",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "checked_docs": {
            "host_recipes": str(HOST_RECIPES_DOC.relative_to(REPO_ROOT)),
            "quickstart": str(QUICKSTART_DOC.relative_to(REPO_ROOT)),
            "launch": str(LAUNCH_DOC.relative_to(REPO_ROOT)),
        },
        "host_checks": host_checks,
        "phrase_checks": phrase_checks,
        "cross_links": cross_links,
        "missing": missing,
        "pass_criteria": {
            "all_inventory_hosts_documented": not missing["hosts"],
            "claim_boundary_phrases_present": not missing["phrases"],
            "launch_and_quickstart_link_host_recipes": not missing["cross_links"],
        },
    }


def read_doc(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_host(candidate: dict[str, Any], doc_text: str) -> dict[str, Any]:
    host_id = candidate["id"]
    display_name = candidate["display_name"]
    executable = candidate["executable"]
    present = host_id in doc_text and display_name in doc_text and executable in doc_text
    return {
        "id": host_id,
        "display_name": display_name,
        "executable": executable,
        "present": present,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
