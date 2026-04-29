from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .state_store import RunRecord, build_run_evidence


@dataclass(frozen=True)
class HostCapabilityReport:
    host_id: str
    ok: bool
    capabilities: list[str]
    limitations: list[str]
    claim_boundary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_id": self.host_id,
            "ok": self.ok,
            "capabilities": self.capabilities,
            "limitations": self.limitations,
            "claim_boundary": self.claim_boundary,
        }


@dataclass(frozen=True)
class HostTurnResult:
    ok: bool
    output: dict[str, Any]
    raw_text: str
    claim_boundary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "output": self.output,
            "raw_text": self.raw_text,
            "claim_boundary": self.claim_boundary,
        }


class HostAdapter(ABC):
    host_id: str

    @abstractmethod
    def validate_capabilities(self) -> HostCapabilityReport:
        raise NotImplementedError

    @abstractmethod
    def prepare_session(self, run: RunRecord, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def execute_turn(self, prepared_session: dict[str, Any]) -> HostTurnResult:
        raise NotImplementedError

    @abstractmethod
    def collect_result(self, turn_result: HostTurnResult) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def report_evidence(self, run: RunRecord, input_data: dict[str, Any], result: HostTurnResult) -> dict[str, Any]:
        raise NotImplementedError


class FixtureHostAdapter(HostAdapter):
    host_id = "fixture"

    def __init__(self, fixture_output: dict[str, Any] | None = None) -> None:
        self.fixture_output = fixture_output or {
            "status": "fixture_passed",
            "message": "Fixture adapter returned deterministic local output.",
        }
        self.claim_boundary = {
            "local_first": True,
            "host_live": "fixture_only",
            "provider_live": "not_claimed",
            "notes": [
                "This adapter proves the host adapter contract shape only.",
                "It is not host-live validation and not provider-live validation.",
            ],
        }

    def validate_capabilities(self) -> HostCapabilityReport:
        return HostCapabilityReport(
            host_id=self.host_id,
            ok=True,
            capabilities=["prepare_session", "execute_turn", "collect_result", "report_evidence"],
            limitations=["fixture_only", "no_real_host_process", "no_provider_call"],
            claim_boundary=self.claim_boundary,
        )

    def prepare_session(self, run: RunRecord, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "workflow": run.workflow,
            "input": payload,
            "host_id": self.host_id,
        }

    def execute_turn(self, prepared_session: dict[str, Any]) -> HostTurnResult:
        output = dict(self.fixture_output)
        output["run_id"] = prepared_session["run_id"]
        output["workflow"] = prepared_session["workflow"]
        return HostTurnResult(
            ok=True,
            output=output,
            raw_text="fixture host adapter output",
            claim_boundary=self.claim_boundary,
        )

    def collect_result(self, turn_result: HostTurnResult) -> dict[str, Any]:
        return turn_result.to_dict()

    def report_evidence(self, run: RunRecord, input_data: dict[str, Any], result: HostTurnResult) -> dict[str, Any]:
        evidence = build_run_evidence(
            run=run,
            action="fixture-host-adapter",
            input_data=input_data,
            claim_boundary=result.claim_boundary,
            host=self.host_id,
            provider_lane="not_required",
        )
        evidence["adapter_result_ok"] = result.ok
        return evidence
