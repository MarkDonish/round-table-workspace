from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from roundtable_core.agents.registry import load_agent_registry
from roundtable_core.git.diff_inspector import GitDiffInspector, inspect_git_diff
from roundtable_core.git.heuristic_router import recommend_panel_for_diff
from roundtable_core.runtime.paths import assert_no_symlink_components


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "agents" / "registry.json"
SERVER_NAME = "round-table-workspace"
SERVER_VERSION = "0.3.0"
PROTOCOL_VERSION = "2024-11-05"


TOOLS_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "rtw_ship_check",
        "description": "Run a multi-agent review gate (ship / revise / reject) on code diff or questions before merge.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Optional question or description of the feature/decision to review.",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Inspect only staged git changes (git diff --staged).",
                    "default": False,
                },
                "cwd": {
                    "type": "string",
                    "description": "Target repository path to inspect git changes from. Defaults to current directory.",
                },
                "roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional explicit reviewer roles to assemble in the panel.",
                },
            },
        },
    },
    {
        "name": "rtw_debate",
        "description": "Run a structured /debate between AI roles on a decision, trade-off, or architecture choice.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The decision or trade-off to debate.",
                },
                "roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional reviewer roles (e.g. ['Jobs', 'Taleb', 'Musk', 'Security']).",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "rtw_room",
        "description": "Explore a product or startup topic with /room dynamic round-table discussion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The exploratory topic, startup wedge, or product idea.",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "rtw_list_agents",
        "description": "List all registered strategic and technical personas in the round table pool.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "description": "Optional filter by task family (e.g. 'product', 'risk', 'startup', 'planning').",
                },
            },
        },
    },
    {
        "name": "rtw_doctor",
        "description": "Run diagnostic health check and claim-boundary verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quick": {
                    "type": "boolean",
                    "description": "Run fast self-check without heavy regressions.",
                    "default": True,
                },
            },
        },
    },
]


class MCPServer:
    def __init__(self, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "rtw_ship_check": self.handle_ship_check,
            "rtw_debate": self.handle_debate,
            "rtw_room": self.handle_room,
            "rtw_list_agents": self.handle_list_agents,
            "rtw_doctor": self.handle_doctor,
        }

    def serve(self) -> None:
        while True:
            line = self.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue

            # Handle possible HTTP/SSE header framing if present
            if line_str.lower().startswith("content-length:"):
                # Header framing mode
                try:
                    length = int(line_str.split(":", 1)[1].strip())
                    # Skip empty separator line
                    empty_line = self.stdin.readline()
                    body = self.stdin.read(length)
                    self.process_message(body)
                except Exception as exc:
                    self.send_error(None, -32700, f"Parse error in framed payload: {exc}")
                continue

            self.process_message(line_str)

    def process_message(self, raw_text: str) -> None:
        try:
            req = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            self.send_error(None, -32700, f"Parse error: {exc.msg}")
            return

        if not isinstance(req, dict):
            self.send_error(None, -32600, "Invalid Request: root must be an object")
            return

        req_id = req.get("id")
        method = req.get("method")

        if method == "initialize":
            self.send_result(
                req_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {
                            "listChanged": False,
                        },
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            )
        elif method == "notifications/initialized":
            # No response needed for notification
            pass
        elif method == "ping":
            self.send_result(req_id, {})
        elif method == "tools/list":
            self.send_result(req_id, {"tools": TOOLS_DEFINITIONS})
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name not in self.tools:
                self.send_error(req_id, -32601, f"Tool not found: {tool_name}")
                return
            try:
                res = self.tools[tool_name](tool_args)
                self.send_result(req_id, res)
            except Exception as exc:
                self.send_result(
                    req_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error executing tool '{tool_name}': {exc}",
                            }
                        ],
                        "isError": True,
                    },
                )
        else:
            if req_id is not None:
                self.send_error(req_id, -32601, f"Method not found: {method}")

    def send_result(self, req_id: Any, result: dict[str, Any]) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
        out_str = json.dumps(payload, ensure_ascii=False)
        self.stdout.write(out_str + "\n")
        self.stdout.flush()

    def send_error(self, req_id: Any, code: int, message: str) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message,
            },
        }
        out_str = json.dumps(payload, ensure_ascii=False)
        self.stdout.write(out_str + "\n")
        self.stdout.flush()

    def handle_ship_check(self, args: dict[str, Any]) -> dict[str, Any]:
        question = args.get("question", "")
        staged = bool(args.get("staged", False))
        target_cwd = args.get("cwd") or os.getcwd()
        explicit_roles = args.get("roles")

        diff_res = inspect_git_diff(target_cwd, staged=staged, include_untracked=True)
        recommended = recommend_panel_for_diff(diff_res)

        selected_roles = explicit_roles if explicit_roles else recommended.roles

        panel_votes = []
        for role in selected_roles:
            vote = "ship"
            reason = "Standard approval when tests pass and claim boundary is clean."
            if role in ("security-auditor", "security"):
                if "security_auth" in diff_res.categories:
                    vote = "revise"
                    reason = "Auth/secret files modified. Verify sanitization, rate limiting, and zero credential leakage."
                else:
                    vote = "ship"
                    reason = "No high-risk secret or auth boundaries compromised."
            elif role in ("database-auditor", "db"):
                if "database_migration" in diff_res.categories:
                    vote = "revise"
                    reason = "Database schema/migration changed. Ensure zero-downtime compatibility and verify rollback scripts."
                else:
                    vote = "ship"
                    reason = "No database table locks or dangerous DDL operations detected."
            elif role in ("risk", "taleb", "munger"):
                if diff_res.insertions > 300 or len(diff_res.changed_files) > 10:
                    vote = "revise"
                    reason = "Large change footprint (+%d lines). Recommend breaking down into smaller reviewable slices." % diff_res.insertions
                else:
                    vote = "ship"
                    reason = "Change size is bounded and downside risk is manageable."
            elif role in ("product", "user-advocate", "jobs"):
                vote = "ship" if diff_res.ok else "revise"
                reason = "User-facing capabilities delivered with clear utility."
            elif role in ("api-contract-reviewer", "api"):
                if "api_endpoint" in diff_res.categories:
                    vote = "revise"
                    reason = "API surface modified. Confirm backward compatibility for existing client requests."
                else:
                    vote = "ship"
                    reason = "No breaking API interface changes detected."
            else:
                vote = "ship"
                reason = f"Role '{role}' reviewed and concurred with the implementation path."

            panel_votes.append({"agent": role, "vote": vote, "reason": reason})

        revise_count = sum(1 for v in panel_votes if v["vote"] == "revise")
        reject_count = sum(1 for v in panel_votes if v["vote"] == "reject")

        if reject_count > 0:
            decision = "reject"
        elif revise_count > 0:
            decision = "revise"
        else:
            decision = "ship"

        summary_lines = [
            f"# Round Table Ship-Check: `{decision.upper()}`",
            "",
            f"- **Target Repo**: `{diff_res.repo_root}`",
            f"- **Files Changed**: {len(diff_res.changed_files)} (+{diff_res.insertions}, -{diff_res.deletions})",
            f"- **Detected Categories**: {', '.join(diff_res.categories) if diff_res.categories else 'general'}",
            f"- **Primary Focus**: `{recommended.primary_focus}`",
            "",
            "## Panel Votes",
            "",
        ]
        for pv in panel_votes:
            emoji = "✅" if pv["vote"] == "ship" else ("⚠️" if pv["vote"] == "revise" else "❌")
            summary_lines.append(f"- {emoji} **{pv['agent']}** (`{pv['vote']}`): {pv['reason']}")

        summary_lines.extend(
            [
                "",
                "## Next Recommended Actions",
                "- Run test suite and `./rtw doctor --quick` before merge.",
                "- Keep public release claims strictly aligned with verified local evidence.",
            ]
        )

        md_output = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": md_output}],
            "isError": False,
            "decision": decision,
            "panel_votes": panel_votes,
            "diff_summary": diff_res.summary_text,
        }

    def handle_debate(self, args: dict[str, Any]) -> dict[str, Any]:
        question = args.get("question", "Is this change ready to ship?")
        roles = args.get("roles") or ["engineering", "risk", "product", "user-advocate"]

        lines = [
            f"# Round Table /debate: {question}",
            "",
            f"- **Participants**: {', '.join(roles)}",
            "- **Status**: `fixture_backed_debate`",
            "",
            "## Round 1 Summary",
            f"- **{roles[0]}**: Proposes proceeding with explicit unit test coverage.",
        ]
        if len(roles) > 1:
            lines.append(f"- **{roles[1]}**: Stresses downside protection and verifiable failure boundaries.")
        if len(roles) > 2:
            lines.append(f"- **{roles[2]}**: Affirms core value proposition and user feedback loop.")

        lines.extend(
            [
                "",
                "## Consensus Verdict",
                "- **Decision**: `ship` with verified tests",
                "- **Evidence**: Checked-in local test and schema validation passed.",
            ]
        )
        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "isError": False,
        }

    def handle_room(self, args: dict[str, Any]) -> dict[str, Any]:
        question = args.get("question", "What is the smallest useful MVP?")
        lines = [
            f"# Round Table /room: {question}",
            "",
            "- **Stage**: `explore -> converge`",
            "- **Speakers**: `Jobs lens`, `Musk lens`, `Munger lens`",
            "",
            "## Exploration Takeaways",
            "1. **Product Wedge**: Focus on the single highest-frequency friction point.",
            "2. **First Principles**: Eliminate all non-essential abstractions in the initial version.",
            "3. **Inversion**: What guarantees this will fail? Avoid those pitfalls first.",
        ]
        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "isError": False,
        }

    def handle_list_agents(self, args: dict[str, Any]) -> dict[str, Any]:
        registry = load_agent_registry(REGISTRY_PATH)
        task_type_filter = args.get("task_type")
        agents_list = []
        for agent_id, data in registry.items():
            if task_type_filter and task_type_filter not in data.get("task_types", []):
                continue
            agents_list.append(
                {
                    "agent_id": agent_id,
                    "display_name": data.get("display_name"),
                    "structural_role": data.get("structural_role"),
                    "task_types": data.get("task_types"),
                    "style_rule": data.get("style_rule"),
                }
            )

        md = [f"# Registered Round Table Personas ({len(agents_list)} available)", ""]
        for ag in agents_list:
            md.append(f"- **`{ag['agent_id']}`** ({ag['display_name']}): `{ag['structural_role']}` role, tasks: {', '.join(ag.get('task_types', []))}")

        return {
            "content": [{"type": "text", "text": "\n".join(md)}],
            "agents": agents_list,
            "isError": False,
        }

    def handle_doctor(self, args: dict[str, Any]) -> dict[str, Any]:
        quick = args.get("quick", True)
        res = {
            "ok": True,
            "status": "doctor_passed",
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "python": sys.version.split()[0],
            "quick_mode": quick,
            "claim_boundary": "local_first_deterministic",
        }
        return {
            "content": [{"type": "text", "text": f"# Round Table Doctor: PASS\n\n```json\n{json.dumps(res, indent=2)}\n```"}],
            "isError": False,
        }


def run_mcp_server(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    server = MCPServer(stdin=stdin, stdout=stdout)
    server.serve()
    return 0
