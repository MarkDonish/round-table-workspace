from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"


class GenericAgentExecutorSecurityTest(unittest.TestCase):
    def load_executor(self) -> object:
        if str(RUNTIME_DIR) not in sys.path:
            sys.path.insert(0, str(RUNTIME_DIR))
        spec = importlib.util.spec_from_file_location("generic_agent_executor_test", RUNTIME_DIR / "generic_agent_executor.py")
        if spec is None or spec.loader is None:
            raise AssertionError("Cannot load generic_agent_executor.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def load_local_codex_executor(self) -> object:
        if str(RUNTIME_DIR) not in sys.path:
            sys.path.insert(0, str(RUNTIME_DIR))
        spec = importlib.util.spec_from_file_location("local_codex_executor_security_test", RUNTIME_DIR / "local_codex_executor.py")
        if spec is None or spec.loader is None:
            raise AssertionError("Cannot load local_codex_executor.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_trace_and_error_payload_redact_token_like_values(self) -> None:
        executor = self.load_executor()
        openai_key = "sk-proj-1234567890abcdefSECRET"
        github_token = "ghp_1234567890abcdefSECRET"
        bearer = "Bearer abcdef1234567890SECRET"
        json_secret = "json-secret-1234567890"
        basic = "Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signatureSECRET"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "emit_secret_failure.py"
            script_path.write_text(
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import sys",
                        f"print('stdout token {openai_key}')",
                        f"print('stderr token {bearer}', file=sys.stderr)",
                        f"print('{basic}', file=sys.stderr)",
                        f"print('{jwt}')",
                        "sys.exit(2)",
                    ]
                ),
                encoding="utf-8",
            )
            trace_base = temp_path / "agent-run"
            command = f"{sys.executable} {script_path} --token {github_token} --api-key {json_secret}"

            with self.assertRaises(executor.GenericAgentExecutorError) as captured:
                executor.run_generic_agent_prompt(
                    task_prompt=f"Return JSON with password: {json_secret}",
                    prompt_input={"mode": "redaction-test", "api_key": json_secret},
                    repo_root=REPO_ROOT,
                    command=command,
                    host_name="generic_cli",
                    timeout_seconds=5,
                    trace_base=trace_base,
                    extra_env=None,
                    execution_metadata={"test": "redaction"},
                )

            serialized = executor.serialize_prompt_executor_error(captured.exception, trace_base=trace_base)
            checked_text = json.dumps(serialized, ensure_ascii=False)
            for suffix in [
                ".agent-stdout.txt",
                ".agent-stderr.txt",
                ".agent-command.json",
                ".agent-trace.json",
                ".agent-task-prompt.md",
                ".agent-input.json",
            ]:
                checked_text += "\n" + Path(f"{trace_base}{suffix}").read_text(encoding="utf-8")

        for raw_secret in [openai_key, github_token, bearer, json_secret, basic, jwt]:
            self.assertNotIn(raw_secret, checked_text)
        self.assertIn("[REDACTED]", checked_text)

    def test_success_trace_redacts_output_and_last_message(self) -> None:
        executor = self.load_executor()
        openai_key = "sk-proj-success1234567890SECRET"
        json_secret = "success-json-secret-1234567890"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "emit_secret_success.py"
            script_path.write_text(
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import json",
                        "import os",
                        f"payload = {{'ok': True, 'decision': 'revise', 'api_key': '{json_secret}', 'note': '{openai_key}'}}",
                        "output = os.environ['ROUND_TABLE_OUTPUT_JSON']",
                        "open(output, 'w', encoding='utf-8').write(json.dumps(payload))",
                    ]
                ),
                encoding="utf-8",
            )
            trace_base = temp_path / "agent-run-success"
            response = executor.run_generic_agent_prompt(
                task_prompt=f"Return JSON with {openai_key}",
                prompt_input={"mode": "redaction-test", "password": json_secret},
                repo_root=REPO_ROOT,
                command=f"{sys.executable} {script_path}",
                host_name="generic_cli",
                timeout_seconds=5,
                trace_base=trace_base,
                extra_env=None,
                execution_metadata={"test": "redaction-success"},
            )
            self.assertIn(openai_key, response)

            checked_text = ""
            for suffix in [
                ".agent-output.json",
                ".agent-last-message.txt",
                ".agent-task-prompt.md",
                ".agent-input.json",
                ".agent-trace.json",
            ]:
                checked_text += "\n" + Path(f"{trace_base}{suffix}").read_text(encoding="utf-8")

        self.assertNotIn(openai_key, checked_text)
        self.assertNotIn(json_secret, checked_text)
        self.assertIn("[REDACTED]", checked_text)

    def test_local_codex_trace_helpers_redact_token_like_values(self) -> None:
        local_executor = self.load_local_codex_executor()
        token = "ghp_localcodex1234567890SECRET"

        with tempfile.TemporaryDirectory() as temp_dir:
            trace_path = Path(temp_dir) / "child.trace.json"
            stderr_path = Path(temp_dir) / "child.stderr.txt"
            local_executor.write_trace_manifest(trace_path, {"command": ["codex", "exec", "--token", token]})
            local_executor.write_trace_text(stderr_path, f"Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ== {token}")
            details = local_executor.build_local_codex_error_details(
                failure_category="command_failed",
                trace_base=Path(temp_dir) / "child",
                summary=f"api_key: {token}",
            )
            serialized = local_executor.serialize_local_codex_error(
                local_executor.LocalCodexExecutorError(f"failed with {token}", details=details),
                trace_base=Path(temp_dir) / "child",
            )

            checked_text = json.dumps(serialized, ensure_ascii=False)
            checked_text += "\n" + trace_path.read_text(encoding="utf-8")
            checked_text += "\n" + stderr_path.read_text(encoding="utf-8")

        self.assertNotIn(token, checked_text)
        self.assertNotIn("QWxhZGRpbjpvcGVuIHNlc2FtZQ==", checked_text)
        self.assertIn("[REDACTED]", checked_text)


if __name__ == "__main__":
    unittest.main()
