#!/usr/bin/env python3
"""Validate a GAPS v1 ga-process YAML against the v1 JSON Schema.

Structural validation only. Cross-reference integrity, state-machine
soundness, gate decision completeness, and conformance-level gating live
in Phase 2.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "gaps" / "schema" / "v1" / "ga-process.schema.json"

sys.dont_write_bytecode = True


class ValidationError(Exception):
    pass


def load_yaml(path: Path) -> Any:
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print YAML.load_file(ARGV[0]).to_json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValidationError(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_schema(data: Any, schema: dict[str, Any]) -> None:
    errors: list[str] = []

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
        return False

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        if "const" in node_schema and node_data != node_schema["const"]:
            errors.append(f"{path}: expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            errors.append(f"{path}: value {node_data!r} not in enum")
            return
        node_type = node_schema.get("type")
        if isinstance(node_type, list):
            if not any(matches_type(node_data, t) for t in node_type):
                errors.append(f"{path}: type mismatch (expected one of {node_type})")
                return
            node_type = next((t for t in node_type if matches_type(node_data, t)), None)
        if node_type == "object":
            if not isinstance(node_data, dict):
                errors.append(f"{path}: expected object")
                return
            for required_key in node_schema.get("required", []):
                if required_key not in node_data:
                    errors.append(f"{path}: missing required key {required_key!r}")
            properties = node_schema.get("properties", {})
            additional = node_schema.get("additionalProperties", True)
            for key, value in node_data.items():
                if key in properties:
                    check(value, properties[key], f"{path}.{key}")
                elif additional is False:
                    errors.append(f"{path}: unexpected key {key!r}")
                elif isinstance(additional, dict):
                    check(value, additional, f"{path}.{key}")
        elif node_type == "array":
            if not isinstance(node_data, list):
                errors.append(f"{path}: expected array")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                errors.append(f"{path}: minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                errors.append(f"{path}: expected string")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                errors.append(f"{path}: minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                errors.append(f"{path}: does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                errors.append(f"{path}: expected boolean")

    check(data, schema, "$")
    if errors:
        raise ValidationError("\n".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a GAPS v1 ga-process YAML file.")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH, help="Schema path override.")
    args = parser.parse_args()
    try:
        data = load_yaml(args.spec)
        schema = load_json(args.schema)
        validate_against_schema(data, schema)
    except ValidationError as error:
        print(f"FAIL {args.spec}: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"GAPS v1 spec validated: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
