"""JSON Schema 2020-12 subset evaluator used by the v1 validator."""

from __future__ import annotations

import re
from typing import Any

from .errors import ValidationReport


def validate_schema(
    data: Any,
    schema: dict[str, Any],
    report: ValidationReport,
    root_path: str = "$",
    rule: str = "schema",
) -> None:
    def matches_type(value: Any, t: str) -> bool:
        if t == "null":
            return value is None
        if t == "string":
            return isinstance(value, str)
        if t == "boolean":
            return isinstance(value, bool)
        if t == "object":
            return isinstance(value, dict)
        if t == "array":
            return isinstance(value, list)
        if t == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if t == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return False

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        if "const" in node_schema and node_data != node_schema["const"]:
            report.add(rule, path, f"expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            report.add(rule, path, f"value {node_data!r} not in enum")
            return
        node_type = node_schema.get("type")
        if isinstance(node_type, list):
            if not any(matches_type(node_data, t) for t in node_type):
                report.add(rule, path, f"type mismatch (expected one of {node_type})")
                return
            node_type = next((t for t in node_type if matches_type(node_data, t)), None)
        if node_type == "object":
            if not isinstance(node_data, dict):
                report.add(rule, path, "expected object")
                return
            for required_key in node_schema.get("required", []):
                if required_key not in node_data:
                    report.add(rule, path, f"missing required key {required_key!r}")
            properties = node_schema.get("properties", {})
            additional = node_schema.get("additionalProperties", True)
            for key, value in node_data.items():
                if key in properties:
                    check(value, properties[key], f"{path}.{key}")
                elif additional is False:
                    report.add(rule, path, f"unexpected key {key!r}")
                elif isinstance(additional, dict):
                    check(value, additional, f"{path}.{key}")
        elif node_type == "array":
            if not isinstance(node_data, list):
                report.add(rule, path, "expected array")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                report.add(rule, path, f"minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                report.add(rule, path, "expected string")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                report.add(rule, path, f"minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                report.add(rule, path, f"does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                report.add(rule, path, "expected boolean")

    check(data, schema, root_path)
