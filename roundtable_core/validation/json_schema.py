from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchemaValidationResult:
    ok: bool
    schema_path: str
    instance_path: str
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "schema_path": self.schema_path,
            "instance_path": self.instance_path,
            "errors": self.errors,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def validate_file(*, schema_path: Path, instance_path: Path) -> SchemaValidationResult:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    errors = validate_instance(instance=instance, schema=schema)
    return SchemaValidationResult(
        ok=not errors,
        schema_path=str(schema_path),
        instance_path=str(instance_path),
        errors=errors,
    )


def validate_instance(*, instance: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate(instance=instance, schema=schema, root_schema=schema, path="$", errors=errors)
    return errors


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
