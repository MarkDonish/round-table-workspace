#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import chat_completions_executor as provider_executor
import room_e2e_validation as room_validation
import room_debate_e2e_validation as integration_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEBATE_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"
if str(DEBATE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(DEBATE_RUNTIME_DIR))

import debate_e2e_validation as debate_validation


DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "chat-completions-regression"
DEFAULT_ROOM_PORT = 32123
DEFAULT_DEBATE_PORT = 32124
DEFAULT_ROOM_MODEL = "mock-room-model"
DEFAULT_DEBATE_MODEL = "mock-debate-model"
HEALTHCHECK_TIMEOUT_SECONDS = 10.0


class ChatCompletionsRegressionError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_regression(args)
    except (
        ChatCompletionsRegressionError,
        provider_executor.ProviderConfigError,
        room_validation.RoomE2EValidationError,
        debate_validation.DebateE2EValidationError,
        integration_validation.RoomDebateE2EValidationError,
        urllib.error.URLError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the checked-in Chat Completions fallback regression suite by booting local mock "
            "providers for /room and /debate, then validating room, debate allow, debate reject-followup, "
            "and full integration."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted regression evidence.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional stable regression run id.",
    )
    parser.add_argument(
        "--room-mock-port",
        type=int,
        default=DEFAULT_ROOM_PORT,
        help="Preferred port for the local /room mock provider.",
    )
    parser.add_argument(
        "--debate-mock-port",
        type=int,
        default=DEFAULT_DEBATE_PORT,
        help="Preferred port for the local /debate mock provider.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for the Chat Completions fallback lane.",
    )
    parser.add_argument(
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for the regression suite.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=room_validation.DEFAULT_FOLLOW_UP,
        help="Follow-up /room input for the regression suite.",
    )
    return parser


def run_regression(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"chat-completions-regression-{uuid.uuid4().hex[:8]}"
    regression_dir = state_root / run_id
    regression_dir.mkdir(parents=True, exist_ok=True)

    room_port = pick_port(args.room_mock_port)
    debate_port = pick_port(args.debate_mock_port)
    room_url = f"http://127.0.0.1:{room_port}/v1/chat/completions"
    debate_url = f"http://127.0.0.1:{debate_port}/v1/chat/completions"

    room_env_file = regression_dir / ".env.room.mock"
    debate_env_file = regression_dir / ".env.debate.mock"
    write_env_file(
        room_env_file,
        {
            "ROOM_CHAT_COMPLETIONS_URL": room_url,
            "ROOM_CHAT_COMPLETIONS_MODEL": DEFAULT_ROOM_MODEL,
            "ROOM_PROVIDER_TIMEOUT_SECONDS": "60",
        },
    )
    write_env_file(
        debate_env_file,
        {
            "DEBATE_CHAT_COMPLETIONS_URL": debate_url,
            "DEBATE_CHAT_COMPLETIONS_MODEL": DEFAULT_DEBATE_MODEL,
            "DEBATE_PROVIDER_TIMEOUT_SECONDS": "60",
        },
    )

    room_server_log = regression_dir / "room-mock-provider.log"
    debate_server_log = regression_dir / "debate-mock-provider.log"

    room_server = start_mock_server(
        script_path=RUNTIME_DIR / "mock_chat_completions_server.py",
        port=room_port,
        log_path=room_server_log,
    )
    debate_server = start_mock_server(
        script_path=DEBATE_RUNTIME_DIR / "mock_chat_completions_server.py",
        port=debate_port,
        log_path=debate_server_log,
    )

    try:
        room_mock_ready = wait_for_mock_health(
            server=room_server,
            url=f"http://127.0.0.1:{room_port}/health",
            label="room",
        )
        debate_mock_ready = wait_for_mock_health(
            server=debate_server,
            url=f"http://127.0.0.1:{debate_port}/health",
            label="debate",
        )

        room_provider_preflight = read_provider_preflight(env_file=room_env_file, provider_scope="room")
        debate_provider_preflight = read_provider_preflight(env_file=debate_env_file, provider_scope="debate")

        room_args = argparse.Namespace(
            executor="chat_completions",
            env_file=str(room_env_file),
            fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
            state_root=str(regression_dir / "room"),
            room_id=None,
            topic=args.topic,
            follow_up_input=args.follow_up_input,
            temperature=args.temperature,
            local_codex_preset=room_validation.DEFAULT_LOCAL_CODEX_PRESET,
            local_codex_model=None,
            local_codex_fallback_models=None,
            local_codex_profile=None,
            local_codex_reasoning_effort=None,
            local_codex_sandbox=None,
            local_codex_timeout_seconds=None,
            local_codex_timeout_retries=None,
            local_codex_retry_timeout_multiplier=None,
            local_codex_persist_session=False,
        )
        room_report = room_validation.run_validation(room_args)

        debate_allow_args = argparse.Namespace(
            executor="chat_completions",
            scenario="allow",
            env_file=str(debate_env_file),
            packet_json=None,
            fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
            state_root=str(regression_dir / "debate-allow"),
            debate_id=None,
            temperature=args.temperature,
            local_codex_preset=integration_validation.DEFAULT_LOCAL_CODEX_PRESET,
            local_codex_model=None,
            local_codex_fallback_models=None,
            local_codex_profile=None,
            local_codex_reasoning_effort=None,
            local_codex_sandbox=None,
            local_codex_timeout_seconds=None,
            local_codex_timeout_retries=None,
            local_codex_retry_timeout_multiplier=None,
            local_codex_persist_session=False,
        )
        debate_allow_report = debate_validation.run_validation(debate_allow_args)

        debate_followup_args = argparse.Namespace(
            executor="chat_completions",
            scenario="reject_followup",
            env_file=str(debate_env_file),
            packet_json=None,
            fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
            state_root=str(regression_dir / "debate-followup"),
            debate_id=None,
            temperature=args.temperature,
            local_codex_preset=integration_validation.DEFAULT_LOCAL_CODEX_PRESET,
            local_codex_model=None,
            local_codex_fallback_models=None,
            local_codex_profile=None,
            local_codex_reasoning_effort=None,
            local_codex_sandbox=None,
            local_codex_timeout_seconds=None,
            local_codex_timeout_retries=None,
            local_codex_retry_timeout_multiplier=None,
            local_codex_persist_session=False,
        )
        debate_followup_report = debate_validation.run_validation(debate_followup_args)

        integration_args = argparse.Namespace(
            executor="chat_completions",
            room_env_file=str(room_env_file),
            debate_env_file=str(debate_env_file),
            room_fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
            debate_fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
            state_root=str(regression_dir / "integration"),
            flow_id=None,
            topic=args.topic,
            follow_up_input=args.follow_up_input,
            scenario="reject_followup",
            temperature=args.temperature,
            local_codex_preset=integration_validation.DEFAULT_LOCAL_CODEX_PRESET,
            local_codex_model=None,
            local_codex_fallback_models=None,
            local_codex_profile=None,
            local_codex_reasoning_effort=None,
            local_codex_sandbox=None,
            local_codex_timeout_seconds=None,
            local_codex_timeout_retries=None,
            local_codex_retry_timeout_multiplier=None,
            local_codex_persist_session=False,
        )
        integration_report = integration_validation.run_validation(integration_args)

        report = {
            "ok": True,
            "action": "chat-completions-regression",
            "run_id": run_id,
            "provider_lane": "mock_provider_fallback",
            "artifacts": {
                "regression_dir": str(regression_dir),
                "regression_report": str(regression_dir / "chat-completions-regression-report.json"),
                "room_env_file": str(room_env_file),
                "debate_env_file": str(debate_env_file),
                "room_mock_log": str(room_server_log),
                "debate_mock_log": str(debate_server_log),
                "room_validation_report": str(Path(room_report["artifacts"]["room_dir"]) / "validation-report.json"),
                "debate_allow_validation_report": str(Path(debate_allow_report["artifacts"]["debate_dir"]) / "validation-report.json"),
                "debate_followup_validation_report": str(Path(debate_followup_report["artifacts"]["debate_dir"]) / "validation-report.json"),
                "integration_report": integration_report["artifacts"]["integration_report"],
            },
            "checks": {
                "room_mock_health": room_mock_ready,
                "debate_mock_health": debate_mock_ready,
                "room_provider_preflight": room_provider_preflight,
                "debate_provider_preflight": debate_provider_preflight,
                "room": room_report,
                "debate_allow": debate_allow_report,
                "debate_reject_followup": debate_followup_report,
                "integration": integration_report,
            },
            "pass_criteria": {
                "room_mock_ready": bool(room_mock_ready.get("ready")),
                "debate_mock_ready": bool(debate_mock_ready.get("ready")),
                "room_provider_ready": bool(room_provider_preflight.get("ready")),
                "debate_provider_ready": bool(debate_provider_preflight.get("ready")),
                "room_passed": all(bool(value) for value in room_report["pass_criteria"].values()),
                "debate_allow_passed": debate_validation.debate_report_passed(debate_allow_report),
                "debate_followup_passed": debate_validation.debate_report_passed(debate_followup_report),
                "integration_passed": bool(integration_report["pass_criteria"]["full_chain_passed"]),
            },
        }
        report["pass_criteria"]["full_suite_passed"] = all(bool(value) for value in report["pass_criteria"].values())
        write_json(regression_dir / "chat-completions-regression-report.json", report)
        return report
    finally:
        stop_server(room_server)
        stop_server(debate_server)


def pick_port(preferred_port: int) -> int:
    preferred = try_bind_port(preferred_port)
    if preferred is not None:
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def try_bind_port(port: int) -> int | None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return None
    return port


def start_mock_server(*, script_path: Path, port: int, log_path: Path) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(script_path), "--port", str(port)],
        cwd=REPO_ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return {
        "process": process,
        "log_path": str(log_path),
        "script_path": str(script_path),
        "port": port,
        "log_handle": log_handle,
    }


def wait_for_mock_health(*, server: dict[str, Any], url: str, label: str) -> dict[str, Any]:
    deadline = time.time() + HEALTHCHECK_TIMEOUT_SECONDS
    process: subprocess.Popen[str] = server["process"]
    while time.time() < deadline:
        if process.poll() is not None:
            raise ChatCompletionsRegressionError(
                f"{label} mock provider exited before becoming healthy. See {server['log_path']}"
            )
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            return {
                "ready": True,
                "label": label,
                "health_url": url,
                "payload": payload,
                "port": server["port"],
                "log_path": server["log_path"],
            }
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError):
            time.sleep(0.25)
    raise ChatCompletionsRegressionError(
        f"{label} mock provider did not become healthy within {HEALTHCHECK_TIMEOUT_SECONDS:.1f}s. See {server['log_path']}"
    )


def read_provider_preflight(*, env_file: Path, provider_scope: str) -> dict[str, Any]:
    env = provider_executor.load_env_file(env_file)
    config = provider_executor.read_provider_config(env, provider_scope=provider_scope)
    return {
        "ready": True,
        "provider_scope": provider_scope,
        "env_file": str(env_file),
        "url": provider_executor.mask_value(config["url"]),
        "model": provider_executor.mask_value(config["model"]),
        "auth_configured": bool(config.get("auth_bearer")),
        "timeout_seconds": config["timeout_seconds"],
    }


def write_env_file(path: Path, variables: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{key}={value}\n" for key, value in variables.items())
    path.write_text(content, encoding="utf-8")


def stop_server(server: dict[str, Any]) -> None:
    process: subprocess.Popen[str] = server["process"]
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    log_handle = server.get("log_handle")
    if log_handle is not None and not log_handle.closed:
        log_handle.close()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
