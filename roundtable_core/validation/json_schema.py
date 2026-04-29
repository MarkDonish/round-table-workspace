from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional dependency path depends on local install.
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - the repo keeps a no-dependency fallback.
    Draft202012Validator = None


@dataclass(frozen=True)
class SchemaValidationResult:
    ok: bool
    schema_path: str
    instance_path: str
    errors: list[str]
    validator_name: str = "rtw-subset"
    supported_draft: str = "draft-2020-12-subset"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "schema_path": self.schema_path,
            "instance_path": self.instance_path,
            "errors": self.errors,
            "validator_name": self.validator_name,
            "supported_draft": self.supported_draft,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def validate_file(*, schema_path: Path, instance_path: Path) -> SchemaValidationResult:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    errors, validator_name, supported_draft = validate_instance_details(instance=instance, schema=schema)
    return SchemaValidationResult(
        ok=not errors,
        schema_path=str(schema_path),
        instance_path=str(instance_path),
        errors=errors,
        validator_name=validator_name,
        supported_draft=supported_draft,
    )


def validate_instance(*, instance: Any, schema: dict[str, Any]) -> list[str]:
    errors, _, _ = validate_instance_details(instance=instance, schema=schema)
    return errors


def validate_instance_details(*, instance: Any, schema: dict[str, Any]) -> tuple[list[str], str, str]:
    if Draft202012Validator is not None:
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
        return [format_jsonschema_error(error) for error in errors], "jsonschema.Draft202012Validator", "draft-2020-12"

    errors: list[str] = []
    _validate(instance=instance, schema=schema, root_schema=schema, path="$", errors=errors)
    return errors, "rtw-subset", "draft-2020-12-subset"


def _validate(
    *,
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if "$ref" in schema:
        target = resolve_ref(root_schema, str(schema["$ref"]))
        _validate(instance=instance, schema=target, root_schema=root_schema, path=path, errors=errors)
        return

    for child_schema in schema.get("allOf", []):
        if isinstance(child_schema, dict):
            _validate(instance=instance, schema=child_schema, root_schema=root_schema, path=path, errors=errors)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        child_results = validate_schema_candidates(instance, any_of, root_schema, path)
        if not any(not result for result in child_results):
            errors.append(f"{path}: expected to match at least one anyOf schema")

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        child_results = validate_schema_candidates(instance, one_of, root_schema, path)
        pass_count = sum(1 for result in child_results if not result)
        if pass_count != 1:
            errors.append(f"{path}: expected to match exactly one oneOf schema, matched {pass_count}")

    not_schema = schema.get("not")
    if isinstance(not_schema, dict):
        candidate_errors: list[str] = []
        _validate(instance=instance, schema=not_schema, root_schema=root_schema, path=path, errors=candidate_errors)
        if not candidate_errors:
            errors.append(f"{path}: instance must not match forbidden schema")

    if_schema = schema.get("if")
    if isinstance(if_schema, dict):
        condition_errors: list[str] = []
        _validate(instance=instance, schema=if_schema, root_schema=root_schema, path=path, errors=condition_errors)
        then_schema = schema.get("then")
        else_schema = schema.get("else")
        if not condition_errors and isinstance(then_schema, dict):
            _validate(instance=instance, schema=then_schema, root_schema=root_schema, path=path, errors=errors)
        if condition_errors and isinstance(else_schema, dict):
            _validate(instance=instance, schema=else_schema, root_schema=root_schema, path=path, errors=errors)

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {instance!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not matches_type(instance, expected_type):
        errors.append(f"{path}: expected type {expected_type!r}, got {json_type_name(instance)}")
        return

    if isinstance(instance, dict):
        validate_object(instance=instance, schema=schema, root_schema=root_schema, path=path, errors=errors)
    elif isinstance(instance, list):
        validate_array(instance=instance, schema=schema, root_schema=root_schema, path=path, errors=errors)
    elif isinstance(instance, str):
        validate_string(instance=instance, schema=schema, path=path, errors=errors)
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        validate_number(instance=instance, schema=schema, path=path, errors=errors)


def validate_object(
    *,
    instance: dict[str, Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")

    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for key, child_schema in properties.items():
            if key in instance and isinstance(child_schema, dict):
                _validate(
                    instance=instance[key],
                    schema=child_schema,
                    root_schema=root_schema,
                    path=f"{path}.{key}",
                    errors=errors,
                )

    min_properties = schema.get("minProperties")
    if isinstance(min_properties, int) and len(instance) < min_properties:
        errors.append(f"{path}: expected at least {min_properties} properties, got {len(instance)}")

    max_properties = schema.get("maxProperties")
    if isinstance(max_properties, int) and len(instance) > max_properties:
        errors.append(f"{path}: expected at most {max_properties} properties, got {len(instance)}")

    dependent_required = schema.get("dependentRequired", {})
    if isinstance(dependent_required, dict):
        for key, dependents in dependent_required.items():
            if key not in instance or not isinstance(dependents, list):
                continue
            for dependent in dependents:
                if dependent not in instance:
                    errors.append(f"{path}: property {key!r} requires property {dependent!r}")

    additional = schema.get("additionalProperties", True)
    if additional is False and isinstance(properties, dict):
        allowed = set(properties)
        for key in instance:
            if key not in allowed:
                errors.append(f"{path}: unexpected additional property {key!r}")
    elif isinstance(additional, dict) and isinstance(properties, dict):
        for key, value in instance.items():
            if key not in properties:
                _validate(
                    instance=value,
                    schema=additional,
                    root_schema=root_schema,
                    path=f"{path}.{key}",
                    errors=errors,
                )


def validate_array(
    *,
    instance: list[Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(instance) < min_items:
        errors.append(f"{path}: expected at least {min_items} items, got {len(instance)}")

    max_items = schema.get("maxItems")
    if isinstance(max_items, int) and len(instance) > max_items:
        errors.append(f"{path}: expected at most {max_items} items, got {len(instance)}")

    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(instance):
            _validate(
                instance=item,
                schema=item_schema,
                root_schema=root_schema,
                path=f"{path}[{index}]",
                errors=errors,
            )

    if schema.get("uniqueItems") is True:
        seen: set[str] = set()
        for item in instance:
            fingerprint = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if fingerprint in seen:
                errors.append(f"{path}: expected unique array items")
                break
            seen.add(fingerprint)


def validate_string(*, instance: str, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    min_length = schema.get("minLength")
    if isinstance(min_length, int) and len(instance) < min_length:
        errors.append(f"{path}: expected string length >= {min_length}, got {len(instance)}")

    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, instance) is None:
        errors.append(f"{path}: expected string to match pattern {pattern!r}")

    if schema.get("format") == "date-time" and not is_iso_datetime(instance):
        errors.append(f"{path}: expected ISO 8601 date-time string")


def validate_number(*, instance: int | float, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    minimum = schema.get("minimum")
    if isinstance(minimum, (int, float)) and instance < minimum:
        errors.append(f"{path}: expected value >= {minimum}, got {instance}")

    maximum = schema.get("maximum")
    if isinstance(maximum, (int, float)) and instance > maximum:
        errors.append(f"{path}: expected value <= {maximum}, got {instance}")


def resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local JSON Schema refs are supported: {ref}")

    target: Any = root_schema
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or key not in target:
            raise ValueError(f"Unresolvable JSON Schema ref: {ref}")
        target = target[key]

    if not isinstance(target, dict):
        raise ValueError(f"JSON Schema ref does not point to an object: {ref}")
    return target


def matches_type(instance: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(matches_type(instance, item) for item in expected_type)

    if expected_type == "object":
        return isinstance(instance, dict)
    if expected_type == "array":
        return isinstance(instance, list)
    if expected_type == "string":
        return isinstance(instance, str)
    if expected_type == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected_type == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected_type == "boolean":
        return isinstance(instance, bool)
    if expected_type == "null":
        return instance is None
    return False


def json_type_name(instance: Any) -> str:
    if instance is None:
        return "null"
    if isinstance(instance, bool):
        return "boolean"
    if isinstance(instance, dict):
        return "object"
    if isinstance(instance, list):
        return "array"
    if isinstance(instance, str):
        return "string"
    if isinstance(instance, int):
        return "integer"
    if isinstance(instance, float):
        return "number"
    return type(instance).__name__


def is_iso_datetime(value: str) -> bool:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def validate_schema_candidates(
    instance: Any,
    schemas: list[Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[list[str]]:
    results: list[list[str]] = []
    for child_schema in schemas:
        candidate_errors: list[str] = []
        if isinstance(child_schema, dict):
            _validate(instance=instance, schema=child_schema, root_schema=root_schema, path=path, errors=candidate_errors)
        else:
            candidate_errors.append(f"{path}: schema candidate is not an object")
        results.append(candidate_errors)
    return results


def format_jsonschema_error(error: Any) -> str:
    location = "$"
    for part in error.path:
        if isinstance(part, int):
            location += f"[{part}]"
        else:
            location += f".{part}"
    return f"{location}: {error.message}"
