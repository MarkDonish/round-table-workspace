#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Process Round Table review for GitHub Actions PR integration.")
    parser.add_argument("--result-json", required=True, help="Path to rtw ship-check result JSON.")
    parser.add_argument("--markdown", required=True, help="Path to rtw Markdown summary.")
    args = parser.parse_args()

    result_path = Path(args.result_json)
    md_path = Path(args.markdown)

    if not result_path.exists():
        print(f"Error: {result_path} not found", file=sys.stderr)
        return 1

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    decision = str(payload.get("decision", "revise")).lower()
    summary_md = md_path.read_text(encoding="utf-8") if md_path.exists() else render_fallback_md(payload)

    # Set GitHub Actions step outputs if in GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"decision={decision}\n")

    # Append to GitHub Step Summary if available
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write(f"\n{summary_md}\n")

    # Post comment to PR if in GitHub Action with PR event
    token = os.environ.get("GITHUB_TOKEN")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if token and event_path and Path(event_path).exists():
        try:
            event_data = json.loads(Path(event_path).read_text(encoding="utf-8"))
            pr_number = event_data.get("pull_request", {}).get("number")
            repo_full_name = os.environ.get("GITHUB_REPOSITORY")
            if pr_number and repo_full_name:
                post_pr_comment(repo_full_name, pr_number, token, summary_md)
        except Exception as exc:
            print(f"Notice: Could not post PR comment automatically ({exc})", file=sys.stderr)

    fail_on_reject = os.environ.get("FAIL_ON_REJECT", "true").lower() in ("true", "1", "yes")
    fail_on_revise = os.environ.get("FAIL_ON_REVISE", "false").lower() in ("true", "1", "yes")

    if decision == "reject" and fail_on_reject:
        print("❌ Round Table Review decision is REJECT. Workflow failed as requested.", file=sys.stderr)
        return 1
    if decision == "revise" and fail_on_revise:
        print("⚠️ Round Table Review decision is REVISE. Workflow failed as requested.", file=sys.stderr)
        return 1

    return 0


def post_pr_comment(repo: str, pr_number: int, token: str, comment_body: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "RoundTable-Review-Bot",
        "Content-Type": "application/json",
    }
    data = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status in (200, 201):
            print(f"Successfully posted Round Table review comment to PR #{pr_number}")


def render_fallback_md(payload: dict[str, object]) -> str:
    decision = str(payload.get("decision", "revise")).upper()
    lines = [
        f"# 🚦 Round Table Review: `{decision}`",
        "",
        f"- **Action**: `{payload.get('action', 'ship-check')}`",
        f"- **Confidence**: `{payload.get('confidence', 'medium')}`",
        "",
        "## Panel Votes",
        "",
    ]
    for pv in payload.get("panel_votes", []):
        if isinstance(pv, dict):
            lines.append(f"- **{pv.get('agent')}** (`{pv.get('vote')}`): {pv.get('reason')}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
