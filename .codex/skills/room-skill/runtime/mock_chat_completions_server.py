#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import room_runtime as runtime


DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "canonical"
PROMPT_MARKERS = {
    "selection": "# Room Selection Prompt",
    "chat": "# Room Chat Prompt",
    "summary": "# Room Summary Prompt",
    "upgrade": "# Room Upgrade Prompt",
}


class MockProviderError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    fixtures_dir = Path(args.fixtures_dir).expanduser().resolve()
    app = MockChatCompletionsApp(fixtures_dir=fixtures_dir, verbose=args.verbose)
    server = ThreadingHTTPServer((args.host, args.port), app.build_handler())

    print(
        json.dumps(
            {
                "ready": True,
                "host": args.host,
                "port": args.port,
                "url": f"http://{args.host}:{args.port}/v1/chat/completions",
                "fixtures_dir": str(fixtures_dir),
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Serve canonical /room fixtures through a Chat Completions-compatible local mock endpoint."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=32123)
    parser.add_argument(
        "--fixtures-dir",
        default=str(DEFAULT_FIXTURES_DIR),
        help="Fixture directory to serve from.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


class MockChatCompletionsApp:
    def __init__(self, *, fixtures_dir: Path, verbose: bool) -> None:
        self.fixtures_dir = fixtures_dir
        self.verbose = verbose

    def build_handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/health":
                    self._write_json(HTTPStatus.OK, {"ok": True})
                    return
                self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self) -> None:  # noqa: N802
                if self.path != "/v1/chat/completions":
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                    return

                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw_body = self.rfile.read(length).decode("utf-8")
                    body = json.loads(raw_body)
                    payload = app.build_completion(body)
                    self._write_json(HTTPStatus.OK, payload)
                except (MockProviderError, json.JSONDecodeError, ValueError) as exc:
                    self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                if app.verbose:
                    super().log_message(format, *args)

            def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
                encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status.value)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return Handler

    def build_completion(self, body: dict[str, Any]) -> dict[str, Any]:
        messages = body.get("messages")
        if not isinstance(messages, list) or len(messages) < 2:
            raise MockProviderError("Mock provider requires at least 2 messages.")

        system_content = str(messages[0].get("content", ""))
        user_content = str(messages[1].get("content", ""))
        prompt_kind = detect_prompt_kind(system_content)
        prompt_input = parse_prompt_input(user_content)
        fixture_name = resolve_fixture_name(prompt_kind=prompt_kind, prompt_input=prompt_input)
        fixture_payload = runtime.load_json(self.fixtures_dir / fixture_name)
        room_id = extract_room_id(prompt_input)
        materialized = runtime.materialize_placeholders(fixture_payload, {"__ROOM_ID__": room_id})
        completion_text = json.dumps(materialized, ensure_ascii=False, indent=2)

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "mock-room-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": completion_text,
                    },
                    "finish_reason": "stop",
                }
            ],
        }


def detect_prompt_kind(system_content: str) -> str:
    for prompt_kind, marker in PROMPT_MARKERS.items():
        if marker in system_content:
            return prompt_kind
    raise MockProviderError("Could not detect prompt kind from system prompt.")


def parse_prompt_input(user_content: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*\})\s*```", user_content, re.DOTALL)
    if not match:
        raise MockProviderError("Could not parse prompt input JSON from user content.")
    parsed = json.loads(match.group(1))
    if not isinstance(parsed, dict):
        raise MockProviderError("Prompt input must be a JSON object.")
    return parsed


def resolve_fixture_name(*, prompt_kind: str, prompt_input: dict[str, Any]) -> str:
    if prompt_kind == "selection":
        mode = prompt_input.get("mode")
        if mode == "room_full":
            return "room_full.selection.json"
        if mode == "room_turn":
            topic = str(prompt_input.get("topic", ""))
            return "focus_turn.selection.json" if topic.startswith("/focus") else "initial_turn.selection.json"
        raise MockProviderError(f"Unsupported selection mode for mock provider: {mode}")
    if prompt_kind == "chat":
        turn_id = prompt_input.get("turn_id")
        if turn_id == 1:
            return "initial_turn.chat.json"
        if turn_id == 2:
            return "focus_turn.chat.json"
        raise MockProviderError(f"Mock provider only supports turn_id 1-2 for room_chat, got {turn_id}")
    if prompt_kind == "summary":
        return "summary.json"
    if prompt_kind == "upgrade":
        return "upgrade.json"
    raise MockProviderError(f"Unsupported prompt kind: {prompt_kind}")


def extract_room_id(prompt_input: dict[str, Any]) -> str:
    room_state = prompt_input.get("room_state")
    if isinstance(room_state, dict) and isinstance(room_state.get("room_id"), str):
        return room_state["room_id"]
    return "room-mock-placeholder"


if __name__ == "__main__":
    sys.exit(main())
