from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentFactoryTest(unittest.TestCase):
    def invoke_cli(self, argv: list[str]) -> tuple[int, str]:
        from roundtable import cli

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cli.main(argv)
        return code, stdout.getvalue()

    def test_example_agent_bundle_validates(self) -> None:
        from importlib.machinery import SourceFileLoader

        module_path = REPO_ROOT / ".codex" / "skills" / "agent-builder-skill" / "runtime" / "validate_agent_bundle.py"
        module = SourceFileLoader("validate_agent_bundle_test", str(module_path)).load_module()
        report = module.validate_bundle(
            REPO_ROOT / "examples" / "agent-factory" / "duan-yongping.agent.manifest.json",
            REPO_ROOT / "examples" / "agent-factory" / "duan-yongping.roundtable-profile.md",
        )

        self.assertTrue(report["ok"], json.dumps(report, ensure_ascii=False, indent=2))
        self.assertEqual(report["agent_id"], "duan-yongping")

    def test_agent_factory_schemas_validate_examples(self) -> None:
        from roundtable_core.validation import validate_file

        cases = [
            ("schemas/agent-manifest.schema.json", "examples/agent-factory/duan-yongping.agent.manifest.json"),
            ("schemas/agent-registry.schema.json", "config/agent-registry.json"),
            ("schemas/agent-selection-request.schema.json", "examples/agent-factory/selection-request.manual-pool.json"),
        ]
        for schema, fixture in cases:
            result = validate_file(schema_path=REPO_ROOT / schema, instance_path=REPO_ROOT / fixture)
            self.assertTrue(result.ok, result.to_json())

    def test_agent_registry_runtime_lists_and_validates(self) -> None:
        from importlib.machinery import SourceFileLoader

        module_path = REPO_ROOT / ".codex" / "skills" / "agent-builder-skill" / "runtime" / "agent_registry.py"
        module = SourceFileLoader("agent_registry_test", str(module_path)).load_module()

        list_report = module.list_agents(REPO_ROOT / "config" / "agent-registry.json")
        validate_report = module.validate_registry(REPO_ROOT / "config" / "agent-registry.json")

        self.assertTrue(list_report["ok"])
        self.assertGreaterEqual(list_report["agent_count"], 1)
        self.assertTrue(validate_report["ok"], json.dumps(validate_report, ensure_ascii=False, indent=2))

    def test_agent_factory_core_services_cover_registry_and_bundle(self) -> None:
        from roundtable_core.commands import run_agent_list, run_agent_validate

        list_report = run_agent_list()
        registry_report = run_agent_validate()
        explicit_registry_report = run_agent_validate(target="config/agent-registry.json")
        bundle_report = run_agent_validate(
            target="examples/agent-factory/duan-yongping.agent.manifest.json",
            profile="examples/agent-factory/duan-yongping.roundtable-profile.md",
        )

        self.assertTrue(list_report["ok"])
        self.assertEqual(list_report["action"], "agent-registry-list")
        self.assertTrue(registry_report["ok"], json.dumps(registry_report, ensure_ascii=False, indent=2))
        self.assertTrue(explicit_registry_report["ok"], json.dumps(explicit_registry_report, ensure_ascii=False, indent=2))
        self.assertEqual(explicit_registry_report["action"], "agent-registry-validate")
        self.assertTrue(bundle_report["ok"], json.dumps(bundle_report, ensure_ascii=False, indent=2))
        self.assertEqual(bundle_report["action"], "agent-bundle-validate")

    def test_agent_registry_register_duplicate_protection_with_temp_registry(self) -> None:
        from importlib.machinery import SourceFileLoader

        module_path = REPO_ROOT / ".codex" / "skills" / "agent-builder-skill" / "runtime" / "agent_registry.py"
        module = SourceFileLoader("agent_registry_register_test", str(module_path)).load_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            registry = Path(temp_dir) / "agent-registry.json"
            shutil.copyfile(REPO_ROOT / "config" / "agent-registry.json", registry)
            manifest = REPO_ROOT / "examples" / "agent-factory" / "duan-yongping.agent.manifest.json"

            duplicate = module.register_agent(
                registry_path=registry,
                manifest_path=manifest,
                replace=False,
                enable=False,
            )
            replaced = module.register_agent(
                registry_path=registry,
                manifest_path=manifest,
                replace=True,
                enable=False,
            )

            self.assertFalse(duplicate["ok"])
            self.assertTrue(replaced["ok"], json.dumps(replaced, ensure_ascii=False, indent=2))

    def test_rtw_agent_cli_list_and_validate(self) -> None:
        code, output = self.invoke_cli(["agent", "list"])
        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["action"], "agent-registry-list")
        self.assertGreaterEqual(payload["agent_count"], 1)

        code, output = self.invoke_cli(["agent", "validate"])
        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["action"], "agent-registry-validate")
        self.assertTrue(payload["ok"])

        code, output = self.invoke_cli(["agent", "validate", "config/agent-registry.json"])
        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["action"], "agent-registry-validate")
        self.assertTrue(payload["ok"])

    def test_rtw_agent_subcommand_output_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_json = Path(temp_dir) / "agent-list.json"

            code, output = self.invoke_cli(["agent", "list", "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["action"], "agent-registry-list")

            code, output = self.invoke_cli(["agent", "list", "--quiet", "--output-json", str(output_json)])
            self.assertEqual(code, 0)
            self.assertEqual(output, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["action"], "agent-registry-list")

            code, output = self.invoke_cli(["agent", "--quiet", "list"])
            self.assertEqual(code, 0)
            self.assertEqual(output, "")

    def test_rtw_agent_register_uses_core_with_temp_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = Path(temp_dir) / "agent-registry.json"
            shutil.copyfile(REPO_ROOT / "config" / "agent-registry.json", registry)
            manifest = REPO_ROOT / "examples" / "agent-factory" / "duan-yongping.agent.manifest.json"

            code, output = self.invoke_cli(
                [
                    "agent",
                    "--registry",
                    str(registry),
                    "register",
                    str(manifest),
                    "--replace",
                    "--json",
                ]
            )

            self.assertEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["action"], "agent-register")
            self.assertTrue(payload["ok"])

    def test_rtw_agent_register_refuses_symlink_registry_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            real_registry = Path(temp_dir) / "agent-registry-real.json"
            symlink_registry = Path(temp_dir) / "agent-registry-link.json"
            shutil.copyfile(REPO_ROOT / "config" / "agent-registry.json", real_registry)
            symlink_registry.symlink_to(real_registry)
            manifest = REPO_ROOT / "examples" / "agent-factory" / "duan-yongping.agent.manifest.json"

            code, output = self.invoke_cli(
                [
                    "agent",
                    "--registry",
                    str(symlink_registry),
                    "register",
                    str(manifest),
                    "--replace",
                ]
            )

            self.assertEqual(code, 1)
            payload = json.loads(output)
            self.assertEqual(payload["action"], "agent-register")
            self.assertIn("Refusing to write registry through symlink", payload["errors"][0])

    def test_rtw_agent_missing_paths_return_structured_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_registry = Path(temp_dir) / "missing-registry.json"
            missing_custom_registry = Path(temp_dir) / "custom-registry.json"
            missing_manifest = Path(temp_dir) / "missing.agent.manifest.json"

            code, output = self.invoke_cli(["agent", "--registry", str(missing_registry), "list"])
            self.assertEqual(code, 1)
            payload = json.loads(output)
            self.assertEqual(payload["action"], "agent-registry-list")
            self.assertIn("registry does not exist", payload["errors"][0])

            code, output = self.invoke_cli(["agent", "validate", str(missing_custom_registry)])
            self.assertEqual(code, 1)
            payload = json.loads(output)
            self.assertEqual(payload["action"], "agent-registry-validate")
            self.assertIn("registry does not exist", payload["errors"][0])

            code, output = self.invoke_cli(["agent", "validate", str(missing_manifest)])
            self.assertEqual(code, 1)
            payload = json.loads(output)
            self.assertEqual(payload["action"], "agent-bundle-validate")
            self.assertIn("manifest does not exist", payload["manifest_validation"]["errors"][0])


if __name__ == "__main__":
    unittest.main()
