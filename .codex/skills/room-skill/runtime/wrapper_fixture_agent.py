#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import generic_fixture_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture agent that emits deliberately noisy JSON for wrapper validation.")
    parser.add_argument(
        "--mode",
        choices=["markdown", "stdout_noise", "output_file"],
        default="markdown",
        help="Noisy output mode to simulate.",
    )
    args = parser.parse_args()

    task_prompt = sys.stdin.read()
    try:
        payload = build_payload(task_prompt)
    except Exception as exc:  # This script is test-only; keep failures explicit.
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output_text = render_noisy_payload(payload, mode=args.mode)
    if args.mode == "output_file":
        output_path = os.environ.get("ROUND_TABLE_OUTPUT_JSON", "").strip()
        if not output_path:
            print("ROUND_TABLE_OUTPUT_JSON is required for output_file mode.", file=sys.stderr)
            return 1
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output_text, encoding="utf-8")
        print("fixture wrote noisy JSON to output file")
    else:
        sys.stdout.write(output_text)
    return 0


def build_payload(task_prompt: str) -> dict[str, Any]:
    if "generic_agent_exec" in task_prompt:
        return {"ok": True, "mode": "generic_agent_exec"}
    prompt_path = generic_fixture_agent.extract_prompt_path(task_prompt)
    prompt_input = generic_fixture_agent.extract_structured_input(task_prompt)
    if prompt_path is None or prompt_input is None:
        return {"ok": True, "mode": "wrapper_fixture_agent"}
    return generic_fixture_agent.load_fixture_payload(prompt_path=prompt_path, prompt_input=prompt_input)


def render_noisy_payload(payload: dict[str, Any], *, mode: str) -> str:
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2)
    if mode == "markdown":
        return "Here is the requested JSON:\n\n```json\n" + raw_json + "\n```\n"
    if mode == "stdout_noise":
        return "[agent-log] starting response\n" + raw_json + "\n[agent-log] completed\n"
    if mode == "output_file":
        return "The final object is below.\n\n```json\n" + raw_json + "\n```\n"
    raise ValueError(f"unsupported wrapper fixture mode: {mode}")


if __name__ == "__main__":
    sys.exit(main())
