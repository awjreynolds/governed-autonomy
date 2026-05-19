#!/usr/bin/env python3
"""Validate GAPS-native catalogs and OSCAL control catalogs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
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
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValidationError(f"unable to read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid JSON in {path}: {error}") from error


def validate_against_schema(data: Any, schema: dict[str, Any], where: str) -> None:
    """Tiny JSON Schema subset evaluator covering the patterns this repo uses.

    Supports: type, required, properties, additionalProperties (False or schema),
    items, minItems, minLength, enum, const, pattern.
    """
    errors: list[str] = []

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        if "const" in node_schema and node_data != node_schema["const"]:
            errors.append(f"{path}: expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            errors.append(f"{path}: value {node_data!r} not in enum")
            return
        node_type = node_schema.get("type")
        if node_type == "object":
            if not isinstance(node_data, dict):
                errors.append(f"{path}: expected object, got {type(node_data).__name__}")
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
                errors.append(f"{path}: expected array, got {type(node_data).__name__}")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                errors.append(f"{path}: minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                errors.append(f"{path}: expected string, got {type(node_data).__name__}")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                errors.append(f"{path}: minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                errors.append(f"{path}: does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                errors.append(f"{path}: expected boolean")

    check(data, schema, where)
    if errors:
        raise ValidationError("\n".join(errors))


def unique_ids(items: list[dict[str, Any]], key: str, where: str) -> None:
    seen: dict[str, int] = {}
    for item in items:
        ident = item.get(key)
        if ident is None:
            continue
        if ident in seen:
            raise ValidationError(f"{where}: duplicate {key}={ident!r}")
        seen[ident] = 1


def validate(catalogs_root: Path, schemas_root: Path) -> None:
    action_schema = load_json(schemas_root / "action-catalog.schema.json")
    evidence_schema = load_json(schemas_root / "evidence-kinds-catalog.schema.json")
    risk_schema = load_json(schemas_root / "risk-patterns-catalog.schema.json")

    actions = load_yaml(catalogs_root / "actions.yml")
    evidence_kinds = load_yaml(catalogs_root / "evidence-kinds.yml")
    risk_patterns = load_yaml(catalogs_root / "risk-patterns.yml")

    validate_against_schema(actions, action_schema, "actions.yml")
    validate_against_schema(evidence_kinds, evidence_schema, "evidence-kinds.yml")
    validate_against_schema(risk_patterns, risk_schema, "risk-patterns.yml")

    unique_ids(actions["actions"], "id", "actions.yml")
    unique_ids(evidence_kinds["evidenceKinds"], "id", "evidence-kinds.yml")
    unique_ids(risk_patterns["riskPatterns"], "id", "risk-patterns.yml")

    evidence_ids = {entry["id"] for entry in evidence_kinds["evidenceKinds"]}
    for pattern in risk_patterns["riskPatterns"]:
        for kind in pattern.get("exampleEvidenceKinds", []):
            if kind not in evidence_ids:
                raise ValidationError(
                    f"risk-patterns.yml: pattern {pattern['id']} references unknown evidence kind {kind!r}"
                )

    expected_categories = {
        "data-plane-read",
        "data-plane-draft",
        "data-plane-persist",
        "data-plane-external",
        "control-plane",
        "meta",
        "prohibited-anti-pattern",
    }
    observed = {entry["category"] for entry in actions["actions"]}
    missing = expected_categories - observed
    if missing:
        raise ValidationError(f"actions.yml: missing actions in categories {sorted(missing)}")

    oscal_schema_path = schemas_root / "oscal-catalog.schema.json"
    controls_dir = catalogs_root / "controls"
    if oscal_schema_path.exists() and controls_dir.exists():
        oscal_schema = load_json(oscal_schema_path)
        seen_uuids: dict[str, Path] = {}
        for path in sorted(controls_dir.glob("*.json")):
            catalog = load_json(path)
            validate_against_schema(catalog, oscal_schema, str(path))
            catalog_uuid = catalog["catalog"]["uuid"]
            if catalog_uuid in seen_uuids:
                raise ValidationError(
                    f"OSCAL catalog UUID collision: {seen_uuids[catalog_uuid]} and {path}"
                )
            seen_uuids[catalog_uuid] = path

            control_ids_per_catalog: dict[str, str] = {}
            for group in catalog["catalog"]["groups"]:
                for control in group["controls"]:
                    cid = control["id"]
                    if cid in control_ids_per_catalog:
                        raise ValidationError(f"{path}: duplicate control id {cid!r}")
                    control_ids_per_catalog[cid] = group["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalogs-root",
        type=Path,
        default=ROOT / "gaps" / "catalogs" / "v1",
        help="Directory containing catalogs (default: gaps/catalogs/v1)",
    )
    parser.add_argument(
        "--schemas-root",
        type=Path,
        default=ROOT / "gaps" / "schema" / "v1",
        help="Directory containing meta-schemas (default: gaps/schema/v1)",
    )
    args = parser.parse_args()
    try:
        validate(args.catalogs_root, args.schemas_root)
    except ValidationError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("GAPS v1 catalogs validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
