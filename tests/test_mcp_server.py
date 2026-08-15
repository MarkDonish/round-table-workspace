from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.mcp.server import MCPServer, TOOLS_DEFINITIONS


class MCPServerTest(unittest.TestCase):
    def test_tools_definitions_schema(self) -> None:
        self.assertGreaterEqual(len(TOOLS_DEFINITIONS), 5)
        tool_names = [t["name"] for t in TOOLS_DEFINITIONS]
        self.assertIn("rtw_ship_check", tool_names)
        self.assertIn("rtw_debate", tool_names)
        self.assertIn("rtw_room", tool_names)
        self.assertIn("rtw_list_agents", tool_names)
        self.assertIn("rtw_doctor", tool_names)

    def test_mcp_initialize_and_ping(self) -> None:
        stdin = io.StringIO(
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
            + "\n"
        )
        stdout = io.StringIO()
        server = MCPServer(stdin=stdin, stdout=stdout)
        server.serve()

        responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]["id"], 1)
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "round-table-workspace")
        self.assertEqual(responses[1]["id"], 2)
        self.assertEqual(responses[1]["result"], {})

    def test_mcp_tools_list_and_call(self) -> None:
        stdin = io.StringIO(
            json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}})
            + "\n"
            + json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "tools/call",
                    "params": {"name": "rtw_ship_check", "arguments": {"question": "Should we ship v0.3.0?"}},
                }
            )
            + "\n"
            + json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 12,
                    "method": "tools/call",
                    "params": {"name": "rtw_list_agents", "arguments": {}},
                }
            )
            + "\n"
        )
        stdout = io.StringIO()
        server = MCPServer(stdin=stdin, stdout=stdout)
        server.serve()

        responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(responses), 3)

        # tools/list response
        self.assertEqual(responses[0]["id"], 10)
        self.assertIn("tools", responses[0]["result"])

        # rtw_ship_check response
        self.assertEqual(responses[1]["id"], 11)
        self.assertIn("content", responses[1]["result"])
        self.assertEqual(responses[1]["result"]["isError"], False)
        self.assertIn("Round Table Ship-Check", responses[1]["result"]["content"][0]["text"])

        # rtw_list_agents response
        self.assertEqual(responses[2]["id"], 12)
        self.assertIn("agents", responses[2]["result"])
        self.assertGreaterEqual(len(responses[2]["result"]["agents"]), 14)

    def test_mcp_error_handling(self) -> None:
        stdin = io.StringIO(
            json.dumps({"jsonrpc": "2.0", "id": 99, "method": "unknown_method", "params": {}})
            + "\n"
            + json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {"name": "non_existent_tool", "arguments": {}},
                }
            )
            + "\n"
        )
        stdout = io.StringIO()
        server = MCPServer(stdin=stdin, stdout=stdout)
        server.serve()

        responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]["id"], 99)
        self.assertIn("error", responses[0])
        self.assertEqual(responses[1]["id"], 100)
        self.assertIn("error", responses[1])


if __name__ == "__main__":
    unittest.main()
