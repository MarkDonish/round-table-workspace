#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import generic_agent_adapter_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-generic-agent-json-wrapper-validation"
MODES = ["markdown", "stdout_noise", "output_file"]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = run_validation(args)
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate generic_agent_json_wrapper.py against noisy stdout, markdown, and output-file modes."
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted validation evidence. Defaults outside the repository.",
    )
    parser.add_argument(
        "--mode",
        choices=[*MODES, "all"],
        default="all",
        help="Wrapper fixture mode to validate.",
    )
    parser.add_argument("--output-json", help="Optional path to write this validation report.")
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    selected_modes = MODES if args.mode == "all" else [args.mode]
    mode_reports = []
    for mode in selected_modes:
        command = (
            "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py "
            "--agent-command "
            f"'python3 .codex/skills/room-skill/runtime/wrapper_fixture_agent.py --mode {mode}'"
        )
        validation_args = argparse.Namespace(
            agent_command=command,
            agent_label=f"json_wrapper_{mode}",
            state_root=str(state_root / mode),
            flow_id=None,
            scenario="reject_followup",
            topic=generic_agent_adapter_validation.room_validation.DEFAULT_TOPIC,
            follow_up_input=generic_agent_adapter_validation.room_validation.DEFAULT_FOLLOW_UP,
            timeout_seconds=generic_agent_adapter_validation.generic_executor.DEFAULT_TIMEOUT_SECONDS,
            output_json=None,
        )
        mode_report = generic_agent_adapter_validation.run_validation(validation_args)
        mode_reports.append(
            {
                "mode": mode,
                "command": command,
                "ok": mode_report.get("ok") is True,
                "pass_criteria": mode_report.get("pass_criteria", {}),
                "artifacts": mode_report.get("artifacts", {}),
            }
        )

    pass_criteria = {
        "all_modes_passed": all(item["ok"] for item in mode_reports),
        "validated_modes": selected_modes,
    }
    return {
        "ok": pass_criteria["all_modes_passed"],
        "action": "generic-agent-json-wrapper-validation",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "modes": mode_reports,
        "pass_criteria": pass_criteria,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
